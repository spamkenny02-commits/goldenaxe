"""Freeze matched-target counter proofs and early wait, including rejected clock variants."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

VARIANTS = ['matched-counter', 'stacked-counter', 'stacked-edge', 'fresh-coarse', 'serialized-clock', 'serialized-edge', 'earlier-wait', 'earlier-edge']
PASSED = ['matched-counter', 'stacked-counter', 'stacked-edge', 'serialized-clock', 'earlier-wait', 'earlier-edge']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT / 'analysis/md-z80-psg-counter-v0203'
    assert not out.exists(), 'Immutable archive exists'
    previous_raw = (ROOT / 'analysis/md-z80-psg-shadow-v0203/manifest.json').read_bytes()
    previous = json.loads(previous_raw)
    baseline_name = 'analysis/md_z80_psg_shadow_ready_report.json'
    assert sha((ROOT / baseline_name).read_bytes()) == previous['reports'][baseline_name]
    old = json.loads((ROOT / baseline_name).read_text())
    assert sha((ROOT / 'analysis/md-z80-psg-shadow-v0203/megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()) == old['driver_source_sha256']
    roots = [(ROOT / ('validation/md-z80-psg-' + v)).resolve() for v in VARIANTS]
    reports = {}
    for variant in PASSED:
        name = 'analysis/md_z80_psg_' + variant.replace('-', '_') + '_report.json'
        raw = (ROOT / name).read_bytes()
        report = json.loads(raw)
        reports[name] = sha(raw)
        folder = ROOT / ('validation/md-z80-psg-' + variant)
        for table in ['sources', 'headers']:
            for filename, h in report[table].items():
                assert sha((ROOT / 'megadrive/src' / filename).read_bytes()) == h
        for relative, key in [('driver.bin', 'driver_sha256'),
                              ('driver-source.asm.snapshot', 'driver_source_sha256'),
                              ('out/release/rom.bin', 'kernel_sha256')]:
            assert sha((folder / relative).read_bytes()) == report[key]
        assert len(report['results']) == 2
        for row in report['results']:
            extras = 26
            assert row['done'] and not row['failures'] and row['plain_core_identical']
            assert row['cases'] == 48 and row['bytes'] == 2976 and row['extra_cases'] == extras
            assert row['errors_master'][0] >= 0 and row['errors_master'][1] > 3420
            assert sha((folder / (row['region'] + '-events.json')).read_bytes()) == row['events_sha256']
            assert len(row['rows']) == 48 + extras
            assert sum(x['counter_wraps'] for x in row['rows']) == 1
            assert sum(x['spacing_checks'] for x in row['rows']) == (596 if extras == 26 else 244)
            for case in row['rows']:
                assert case['sample_gap_master'][1] < 17100
                assert case['clock_line_advance'][1] <= 5
                assert case['bus_holds_master'][1] < 6840
            assert sum(x['fast_target_samples'] for x in row['rows']) > 0
            if variant in ['earlier-wait', 'earlier-edge']:
                assert row['prefetched_commands'] == 64 and row['max_prefetched_pending'] == 15
                assert row['errors_master'][1] < 17100
                assert max(x['sample_gap_master'][1] for x in row['rows']) < 17100
    final = roots[-1]
    assert (final / 'driver-source.asm.snapshot').read_bytes() == (ROOT / 'megadrive/z80/md_psg_prefetch_z80.asm').read_bytes()
    assert report['physical_phase_offset'] == 3419
    assert "AssertionError: ('ntsc', 66" in (ROOT / 'validation/z80-psg-fresh-coarse-run.log').read_text()
    assert '17550' in (ROOT / 'validation/z80-psg-serialized-edge-run.log').read_text()
    core = ROOT.parents[1] / 'work/genesis-plus-gx'
    assert sha((core / 'genesis_plus_gx_z80_psg_io_libretro.dll').read_bytes()) == report['observer_core_sha256']
    for name in ['mem68k.c', 'membnk.c', 'vdp_ctrl.c']:
        reference = ROOT / 'validation/md-z80-psg-io-core' / (name + '-original.sha256')
        assert sha((core / 'core' / name).read_bytes()) == reference.read_text().strip()
    prefix, size = (ROOT / 'validation/z80-psg-counter-world-prefix.sha256').read_text().split()
    assert sha((ROOT / 'analysis/world_next.md').read_bytes()[:int(size)]) == prefix
    assert sha((ROOT / 'gaw-megadrive.bin').read_bytes()) == previous['playable_sha256']
    assert sha((ROOT / 'megadrive/out/release/rom.bin').read_bytes()) == previous['playable_sha256']
    paths = {ROOT / name for name in reports}
    paths.update(ROOT / name for name in ['README.md', 'analysis/world_next.md',
        'analysis/md_z80_psg_counter_milestone.md', 'megadrive/z80/md_psg_prefetch_z80.asm',
        'tools/archive_md_z80_counter.py', 'tools/validate_md_z80_psg.py'])
    for root in roots:
        paths.update(p for p in root.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT / 'validation').iterdir()
                 if p.is_file() and p.name.startswith('z80-psg-') and any(v in p.name for v in VARIANTS + ['counter-world']))
    files, compressed, candidates = {}, {}, []
    for path in sorted(paths):
        raw = path.read_bytes()
        h = sha(raw)
        name = path.relative_to(ROOT).as_posix()
        if path.is_relative_to(ROOT / 'validation') or len(raw) > 65536:
            stored = 'objects/' + h + '.gz'
            dest = out / stored
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(gzip.compress(raw, mtime=0))
            encoded = dest.read_bytes()
            assert gzip.decompress(encoded) == raw
            compressed[name] = dict(stored=stored, raw_sha256=h, raw_bytes=len(raw), stored_sha256=sha(encoded))
        else:
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            files[name] = h
        if any(path.is_relative_to(root) for root in roots) and (
                path.suffix in ['.bin', '.out', '.o', '.s', '.d', '.dll']
                or path.name.endswith(('-events.json', '-clock.json'))
                or path.name in ['expected.h', 'psg.h']):
            candidates.append(path)
    manifest = dict(previous_manifest_sha256=sha(previous_raw),
                    playable_sha256=previous['playable_sha256'], reports=reports,
                    deadline_scheduler_accepted=False, production_integration=False,
                    transport_verified=True, selected_variant='earlier-wait', physical_phase_offsets=[0, 3419],
                    files=files, compressed=compressed, removed_verified_generated=[])
    target = out / 'manifest.json'
    target.write_text(json.dumps(manifest, indent=2) + '\n')
    for name, h in files.items():
        assert sha((out / name).read_bytes()) == h
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
    print(len(files), 'source snapshots;', len(compressed), 'compressed references;',
          sum(x['bytes'] for x in manifest['removed_verified_generated']), 'generated bytes removed')


if __name__ == '__main__':
    main()
