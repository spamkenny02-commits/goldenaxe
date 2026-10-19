"""Lossless archive of Z80 latency variants before verified generated cleanup."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

VARIANTS = ['lean-fetch', 'copy-once', 'copy-prepare', 'private-samples', 'private-unroll']
ACCEPTED = ['copy-once', 'private-samples', 'private-unroll']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT / 'analysis/md-z80-psg-latency-v0203'
    assert not out.exists(), 'Immutable archive exists'
    previous = ROOT / 'analysis/md-z80-psg-v0203'
    previous_raw = (previous / 'manifest.json').read_bytes()
    baseline = json.loads(previous_raw)
    old_report = 'analysis/md_z80_psg_report.json'
    assert sha((ROOT / old_report).read_bytes()) == baseline['compressed'][old_report]['raw_sha256']
    roots = [(ROOT / ('validation/md-z80-psg-' + v)).resolve() for v in VARIANTS]
    reports = {}
    for variant in ACCEPTED:
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
        total_spacing = 0
        for row in report['results']:
            assert row['done'] and not row['failures'] and row['plain_core_identical']
            assert row['cases'] == 48 and row['bytes'] == 2976 and row['extra_cases'] == 25
            assert row['errors_master'][0] >= 0 and row['errors_master'][1] > 3420
            assert sha((folder / (row['region'] + '-events.json')).read_bytes()) == row['events_sha256']
            assert len(row['rows']) == 73
            assert sum(x['counter_wraps'] for x in row['rows']) == 1
            for case in row['rows']:
                assert case['sample_gap_master'][1] < 17100
                assert case['clock_line_advance'][1] <= 5
                assert case['bus_holds_master'][1] < 6840
                total_spacing += case['spacing_checks']
        assert total_spacing == 488
    final = ROOT / 'validation/md-z80-psg-private-unroll'
    assert (final / 'driver-source.asm.snapshot').read_bytes() == (ROOT / 'megadrive/z80/md_psg_output_z80.asm').read_bytes()
    failed = json.loads((roots[0] / 'ntsc-events.json').read_text())
    assert failed['observed']['failures'] == 5
    assert '17220' in (ROOT / 'validation/z80-psg-copy-prepare-run.log').read_text()
    core = ROOT.parents[1] / 'work/genesis-plus-gx'
    observer = core / 'genesis_plus_gx_z80_psg_io_libretro.dll'
    assert sha(observer.read_bytes()) == report['observer_core_sha256']
    for name in ['mem68k.c', 'membnk.c', 'vdp_ctrl.c']:
        reference = ROOT / 'validation/md-z80-psg-io-core' / (name + '-original.sha256')
        assert sha((core / 'core' / name).read_bytes()) == reference.read_text().strip()
    prefix, length = (ROOT / 'validation/z80-psg-latency-world-prefix.sha256').read_text().split()
    assert sha((ROOT / 'analysis/world_next.md').read_bytes()[:int(length)]) == prefix
    assert sha((ROOT / 'gaw-megadrive.bin').read_bytes()) == baseline['playable_sha256']
    paths = {ROOT / name for name in reports}
    paths.update(ROOT / name for name in ['README.md', 'analysis/world_next.md',
        'analysis/md_z80_psg_latency_milestone.md', 'megadrive/z80/md_psg_output_z80.asm',
        'tools/archive_md_z80_latency.py', 'tools/validate_md_z80_psg.py'])
    for root in roots:
        paths.update(p for p in root.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT / 'validation').iterdir() if p.is_file()
                 and p.name.startswith('z80-psg-') and any(v in p.name for v in VARIANTS + ['latency-world']))
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
                    playable_sha256=baseline['playable_sha256'], reports=reports,
                    deadline_scheduler_accepted=False, production_integration=False,
                    accepted_transport_variants=ACCEPTED, rejected_variants=['lean-fetch', 'copy-prepare'],
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
