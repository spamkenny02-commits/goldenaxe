"""Freeze PSG transport evidence, preserving the unsuccessful timing experiments."""
import gzip
import hashlib
import json
import subprocess
import sys
from actor_reference import ROOT

FOLDERS = ['md-z80-psg', 'md-z80-bridge', 'md-z80-psg-first-output',
           'md-z80-psg-fast-clock-rejected', 'md-z80-psg-inaccessible-ram',
           'md-z80-psg-io-core']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT / 'analysis/md-z80-psg-v0203'
    assert not out.exists(), 'Immutable archive already exists'
    report = json.loads((ROOT / 'analysis/md_z80_psg_report.json').read_text())
    host = json.loads((ROOT / 'analysis/md_z80_bridge_report.json').read_text())
    folder = ROOT / 'validation/md-z80-psg'
    core = ROOT.parents[1] / 'work/genesis-plus-gx'
    for table in ['sources', 'headers']:
        for name, h in report[table].items():
            assert sha((ROOT / 'megadrive/src' / name).read_bytes()) == h, name
    for name, h in host['sources'].items():
        assert sha((ROOT / 'megadrive/src' / name).read_bytes()) == h, name
    assert host['checks'] == 12016
    assert len(host['rows']) == 2
    for row in host['rows']:
        assert row['descriptors'] == 6000 and row['cursor_wraps'] == 23
        assert row['full_rejections'] == 249
    assert sha((folder / 'out/release/rom.bin').read_bytes()) == report['kernel_sha256']
    assert sha((folder / 'driver.bin').read_bytes()) == report['driver_sha256']
    asm = ROOT / 'megadrive/z80/md_psg_output_z80.asm'
    assert sha(asm.read_bytes()) == report['driver_source_sha256']
    assert (folder / 'driver-source.asm.snapshot').read_bytes() == asm.read_bytes()
    observer = core / 'genesis_plus_gx_z80_psg_io_libretro.dll'
    assert sha(observer.read_bytes()) == report['observer_core_sha256']
    for name in ['mem68k.c', 'membnk.c', 'vdp_ctrl.c']:
        h = (ROOT / 'validation/md-z80-psg-io-core' / (name + '-original.sha256')).read_text().strip()
        assert sha((core / 'core' / name).read_bytes()) == h, name
    assert len(report['results']) == 2
    publications = spacing = 0
    for row in report['results']:
        assert row['done'] and not row['failures'] and row['plain_core_identical']
        assert row['cases'] == 48 and row['extra_cases'] == 25 and row['bytes'] == 2976
        assert row['errors_master'][0] >= 0 and row['errors_master'][1] > 3420
        assert sha((folder / (row['region'] + '-events.json')).read_bytes()) == row['events_sha256']
        assert len(row['rows']) == 73
        assert sum(r['counter_wraps'] for r in row['rows']) == 1
        for case in row['rows']:
            assert case['clock_line_advance'][1] <= 5
            assert case['bus_holds_master'][1] < 6840
            publications += case['clock_publication_checks']
            spacing += case['spacing_checks']
    assert spacing == 488 and publications == 2181
    first = ROOT / 'validation/md-z80-psg-first-output'
    retained = json.loads((first / 'retained-report.json').read_text())
    assert retained['kernel_sha256'] == report['kernel_sha256']
    assert sha((first / 'out/release/rom.bin').read_bytes()) == report['kernel_sha256']
    for row in retained['results']:
        assert not row['failures']
        assert sha((first / (row['region'] + '-events.json')).read_bytes()) == row['events_sha256']
    prefix_hash, prefix_size = (ROOT / 'validation/z80-psg-world-prefix.sha256').read_text().split()
    assert sha((ROOT / 'analysis/world_next.md').read_bytes()[:int(prefix_size)]) == prefix_hash
    playable = sha((ROOT / 'gaw-megadrive.bin').read_bytes())
    assert playable == '7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    assert sha((ROOT / 'megadrive/out/release/rom.bin').read_bytes()) == playable
    paths = {ROOT / 'README.md', ROOT / 'analysis/world_next.md', asm}
    paths.update(ROOT / 'analysis' / name for name in [
        'md_z80_psg_milestone.md', 'md_z80_psg_report.json', 'md_z80_bridge_report.json'])
    paths.update(p for p in (ROOT / 'megadrive/src').iterdir() if p.suffix in ['.c', '.h', '.s', '.inc'])
    paths.update(ROOT / 'tools' / name for name in [
        'archive_md_z80_psg.py', 'validate_md_z80_psg.py', 'validate_md_z80_bridge.py',
        'build_md_io_core.py', 'validate_queued_loading.py', 'validate_native_room_finish.py',
        'validate_reader_timing.py', 'run_core.py', 'actor_reference.py'])
    roots = [(ROOT / 'validation' / name).resolve() for name in FOLDERS]
    for root in roots:
        paths.update(p for p in root.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT / 'validation').iterdir()
                 if p.is_file() and p.name.startswith('z80-psg-'))
    files, compressed, candidates = {}, {}, []

    def retain(name, raw, compress):
        h = sha(raw)
        if compress:
            stored = 'objects/' + h + '.gz'
            dest = out / stored
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(gzip.compress(raw, mtime=0))
            encoded = dest.read_bytes()
            assert gzip.decompress(encoded) == raw
            compressed[name] = dict(stored=stored, raw_sha256=h, raw_bytes=len(raw),
                                    stored_sha256=sha(encoded))
        else:
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            files[name] = h

    for path in sorted(paths):
        name = path.relative_to(ROOT).as_posix()
        retain(name, path.read_bytes(), path.is_relative_to(ROOT / 'validation') or path.stat().st_size > 65536)
        if any(path.is_relative_to(root) for root in roots):
            if (path.suffix in ['.bin', '.out', '.o', '.s', '.d', '.dll']
                    or path.name.endswith(('-events.json', '-clock.json'))
                    or path.name in ['expected.h', 'psg.h']):
                if 'retained-sources' not in path.parts:
                    candidates.append(path)
    retain('emulator/' + observer.name, observer.read_bytes(), True)
    retain('emulator/genesis.c', (core / 'core/genesis.c').read_bytes(), False)
    manifest = dict(playable_sha256=playable, transport_verified=True,
                    deadline_scheduler_accepted=False, production_integration=False,
                    rejected_experiments=['inaccessible-68000-RAM', 'fast-private-clock'],
                    files=files, compressed=compressed, removed_verified_generated=[])
    target = out / 'manifest.json'
    target.write_text(json.dumps(manifest, indent=2) + '\n')
    # Independent archive readback precedes every possible deletion.
    for name, h in files.items():
        assert sha((out / name).read_bytes()) == h
    for value in compressed.values():
        encoded = (out / value['stored']).read_bytes()
        assert sha(encoded) == value['stored_sha256']
        raw = gzip.decompress(encoded)
        assert sha(raw) == value['raw_sha256'] and len(raw) == value['raw_bytes']
    if '--cleanup' in sys.argv:
        for path in candidates:
            resolved = path.resolve()
            assert any(resolved.is_relative_to(root) for root in roots)
            name = resolved.relative_to(ROOT).as_posix()
            assert not subprocess.check_output(['git', 'ls-files', '--', name], cwd=ROOT)
            value = compressed[name]
            raw = resolved.read_bytes()
            assert sha(raw) == value['raw_sha256']
            assert gzip.decompress((out / value['stored']).read_bytes()) == raw
            manifest['removed_verified_generated'].append(dict(path=name, bytes=len(raw)))
            resolved.unlink()
        target.write_text(json.dumps(manifest, indent=2) + '\n')
    print(len(files), 'source snapshots;', len(compressed), 'compressed references;',
          sum(v['bytes'] for v in manifest['removed_verified_generated']), 'generated bytes removed')


if __name__ == '__main__':
    main()
