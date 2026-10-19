"""Freeze rejected native publication experiments before removing generated data."""
from pathlib import Path
import gzip
import hashlib
import json
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ['single-plan-bare', 'early-grant-bare', 'deferred-bare',
            'deferred-service-bare', 'deferred-inline-bare']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT / 'analysis/md-z80-publication-trials-v0203'
    assert not out.exists(), 'Immutable archive already exists'
    previous_raw = (ROOT / 'analysis/md-z80-grants-v0203/manifest.json').read_bytes()
    previous = json.loads(previous_raw)
    paths = set()
    reports = {}
    roots = []
    summaries = []
    for variant in VARIANTS:
        root = (ROOT / ('validation/md-z80-psg-' + variant)).resolve()
        roots.append(root)
        name = 'analysis/md_z80_psg_' + variant.replace('-', '_') + '_report.json'
        raw = (ROOT / name).read_bytes()
        reports[name] = sha(raw)
        report = json.loads(raw)
        assert report['live_loader'] and report['bare'] and report['packet_publication']
        assert report.get('deferred_publication', False) == variant.startswith('deferred')
        assert report.get('source_clock_service', False) == ('service' in variant or 'inline' in variant)
        assert report.get('inline_source_clock_service', False) == ('inline' in variant)
        assert sha((root / 'out/release/rom.bin').read_bytes()) == report['kernel_sha256']
        assert sha((root / 'driver.bin').read_bytes()) == report['driver_sha256']
        driver = (root / 'driver-source.asm.snapshot').read_bytes()
        assert sha(driver) == report['driver_source_sha256']
        assert driver == (ROOT / 'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
        for table in ['sources', 'headers']:
            for filename, expected in report[table].items():
                source = root / (filename + '.snapshot')
                if not source.exists():
                    source = ROOT / 'megadrive/src' / filename
                assert sha(source.read_bytes()) == expected, (variant, filename)
                paths.add(source)
        header = root / 'source_clock.h.snapshot'
        if not header.exists():
            header = ROOT / 'megadrive/src/source_clock.h'
        paths.add(header)
        assert len(report['results']) == 2
        for row in report['results']:
            assert row['done'] and not row['failures'] and not row['failure_code'] and row['plain_core_identical']
            assert row['cases'] == 48 and row['bytes'] == 2976 and not row['extra_cases']
            assert sha((root / (row['region'] + '-events.json')).read_bytes()) == row['events_sha256']
            assert row['errors_master'][0] >= 0
            assert sum(x['spacing_checks'] for x in row['rows']) == 96
            for case in row['rows']:
                assert case['sample_gap_master'][1] < 17100
                assert case['clock_line_advance'][1] <= 5
                assert case['bus_holds_master'][1] < 6840
                assert case['loader_finish_master'] <= case['loader_query_master'] <= case['delivery_finish_master']
            errors = [v for case in row['rows'] for v in case['errors_master']]
            assert len(errors) == 2976
            summaries.append(dict(variant=variant, region=row['region'], maximum=max(errors),
                mean=statistics.mean(errors), median=statistics.median(errors),
                callbacks=sum(x['publisher_callbacks'] for x in row['rows']),
                publisher_marker_time=sum(x['publisher_total_master'] for x in row['rows']),
                source_state_and_bytes_pass=True, selected=False))
        paths.add(ROOT / name)
        paths.update(p for p in root.rglob('*') if p.is_file())
        paths.add(ROOT / ('validation/z80-psg-' + variant + '-run.log'))
    for name in ['gaw-megadrive.bin', 'megadrive/out/release/rom.bin']:
        assert sha((ROOT / name).read_bytes()) == previous['playable_sha256']
    assert sha((ROOT / 'input/original.sms').read_bytes()) == '852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    prefix = json.loads((ROOT / 'validation/z80-publication-trials-world-prefix.json').read_text())
    assert sha((ROOT / 'analysis/world_next.md').read_bytes()[:prefix['bytes']]) == prefix['sha256']
    summary_name = 'analysis/md_z80_psg_publication_trials_report.json'
    summary = dict(results=summaries, selected='grant-eight-bare / grant-eight-proof unchanged',
                   production_integration=False, full_checkpoint_proof_for_trials=False,
                   limits=['All five trials are rejected as timing improvements. Bare final state/IRQ/data/audio/byte checks pass; no full sixteen-checkpoint trial proof or replay regression claim.',
                           'Service attempts outside diagnostic callback markers are not counted in publisher_marker_time. Inline trial additionally used its archived source_clock.h snapshot.'])
    (ROOT / summary_name).write_text(json.dumps(summary, indent=2) + '\n')
    paths.add(ROOT / summary_name)
    for name in ['README.md', 'analysis/world_next.md', 'analysis/md_z80_psg_publication_trials.md',
                 'tools/md_live_z80_kernel.py', 'tools/validate_md_z80_psg.py',
                 'tools/archive_md_z80_publication_trials.py', 'validation/z80-publication-trials-world-prefix.json']:
        paths.add(ROOT / name)
    files = {}
    compressed = {}
    candidates = []
    for path in sorted(paths):
        raw = path.read_bytes()
        name = path.relative_to(ROOT).as_posix()
        digest = sha(raw)
        if path.is_relative_to(ROOT / 'validation') or len(raw) > 65536:
            stored = 'objects/' + digest + '.gz'
            dest = out / stored
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(gzip.compress(raw, mtime=0))
            encoded = dest.read_bytes()
            assert gzip.decompress(encoded) == raw
            compressed[name] = dict(stored=stored, raw_sha256=digest, raw_bytes=len(raw), stored_sha256=sha(encoded))
        else:
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            files[name] = digest
        if any(path.is_relative_to(root) for root in roots) and (
                path.suffix in ['.bin', '.out', '.o', '.s', '.d', '.dll'] or
                path.name.endswith(('-events.json', '-clock.json')) or path.name in ['expected.h', 'psg.h']):
            candidates.append(path)
    manifest = dict(previous_manifest_sha256=sha(previous_raw), playable_sha256=previous['playable_sha256'],
        reports=reports, production_integration=False, all_trials_rejected=True,
        files=files, compressed=compressed, removed_verified_generated=[])
    target = out / 'manifest.json'
    target.write_text(json.dumps(manifest, indent=2) + '\n')
    for name, digest in files.items():
        assert sha((out / name).read_bytes()) == digest
    for item in compressed.values():
        encoded = (out / item['stored']).read_bytes()
        assert sha(encoded) == item['stored_sha256']
        raw = gzip.decompress(encoded)
        assert sha(raw) == item['raw_sha256'] and len(raw) == item['raw_bytes']
    if '--cleanup' in sys.argv:
        for path in candidates:
            resolved = path.resolve()
            assert any(resolved.is_relative_to(root) for root in roots)
            name = resolved.relative_to(ROOT).as_posix()
            assert not subprocess.check_output(['git', 'ls-files', '--', name], cwd=ROOT)
            item = compressed[name]
            raw = resolved.read_bytes()
            assert sha(raw) == item['raw_sha256']
            assert gzip.decompress((out / item['stored']).read_bytes()) == raw
            manifest['removed_verified_generated'].append(dict(path=name, bytes=len(raw)))
            resolved.unlink()
        target.write_text(json.dumps(manifest, indent=2) + '\n')
    print(len(compressed), 'compressed references;', sum(x['bytes'] for x in manifest['removed_verified_generated']), 'generated bytes removed')


if __name__ == '__main__':
    main()
