"""Freeze v0191 noise component, source captures and production evidence."""
import ast
import hashlib
import json
from actor_reference import ROOT


def main():
    folder = ROOT/'analysis/native-audio-noise-v0191'
    items = []

    def preserve(path, name):
        data = path.read_bytes()
        target = folder/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == data, ('immutable evidence differs', name)
        else:
            with target.open('xb') as stream:
                stream.write(data)
        items.append(dict(path=str(name).replace('\\', '/'),
                          sha256=hashlib.sha256(data).hexdigest()))

    digest = hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry = next(e for e in json.loads((ROOT/'versions/index.json').read_text())
                 if e['version'] == 191)
    assert digest == entry['sha256'] and entry['validation'] == 'targeted_checks_passed'
    baseline = ROOT/'analysis/native-audio-sequence-v0190/source-v0190'
    changed = ['sound.inc', 'source_audio_sequence.c', 'source_audio_sequence.h',
               'source_audio_noise.c', 'source_audio_noise.h']
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():
            continue
        if path.name not in changed:
            assert path.read_bytes() == (baseline/path.name).read_bytes(), path.name
        preserve(path, 'source-v0191/'+path.name)
    for name in changed[:3]:
        preserve(baseline/name, 'source-v0190/'+name)
    pending = ['archive_native_audio_noise', 'diagnose_noise_reader_exit',
               'validate_native_audio_noise', 'validate_native_audio_noise_68k',
               'validate_source_native_noise_extensions', 'validate_production_audio_noise',
               'validate_native_audio_sequence', 'validate_native_audio_sequence_68k',
               'validate_inventory_restore', 'validate_production_audio_de',
               'validate_production_audio_priority', 'validate_music', 'validate_sfx',
               'validate_music_fade_dispatch', 'validate_start_menu_audio',
               'validate_start_menu_sfx']
    seen = set()
    while pending:
        name = pending.pop()
        path = ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():
            continue
        seen.add(name)
        preserve(path, 'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                pending.append(node.module.split('.')[0])
            elif isinstance(node, ast.Import):
                pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_noise_report.json', 'native_audio_noise_68k_report.json',
                 'source_native_noise_extensions_report.json',
                 'noise_reader_exit_v0190_diagnostic.json', 'noise_reader_exit_v0191_diagnostic.json',
                 'native_audio_sequence_report.json', 'native_audio_sequence_68k_report.json',
                 'audio_noise_channel_refresh_report.json', 'noise_note_report.json',
                 'native_audio_noise_milestone.md']:
        preserve(ROOT/'analysis'/name, 'analysis/'+name)
    for report in entry['reports']:
        path = ROOT/'versions'/entry['rom']
        preserve(path.parent/report['file'], 'reports/'+report['file'])
    for name in ['native-audio-noise.log', 'native-audio-noise-68k.log',
                 'source-native-noise-extensions.log', 'source-native-noise-flow.log',
                 'native-audio-sequence-v0191.log', 'native-audio-sequence-68k-v0191.log',
                 'noise-reader-exit-v0190.log', 'noise-reader-exit-v0191.log',
                 'build-v0191.log', 'production-audio-noise-v0191.log',
                 'inventory-restore-v0191.log', 'production-audio-de-v0191.log',
                 'production-audio-priority-auto-v0191.log',
                 'production-audio-priority-pal-v0191.log', 'music-v0191.log',
                 'sfx-v0191.log', 'music-fade-v0191.log', 'start-menu-v0191.log',
                 'start-menu-sfx-v0191.log']:
        preserve(ROOT/'validation'/name, 'logs/'+name)
    for name in ['cases.json', 'extension-cases.json', 'compile.log', 'source_audio_noise.dll']:
        preserve(ROOT/'validation/native-audio-noise'/name, 'validation/native-audio-noise/'+name)
    for component in ['noise', 'sequence']:
        for base in sorted((ROOT/f'validation/native-audio-{component}-68k').glob('part-*')):
            for path in sorted((base/'src').iterdir()):
                preserve(path, str(path.relative_to(ROOT)))
            for name in ['build.log', 'out/release/rom.bin', 'out/release/symbol.txt',
                         'auto/capture.json', 'pal/capture.json']:
                preserve(base/name, str((base/name).relative_to(ROOT)))
    for directory in ['audio-noise-extensions', 'production-audio-noise',
                      'noise-reader-exit-v0190', 'noise-reader-exit-v0191',
                      'production-audio-de', 'production-audio-priority',
                      'start-menu-sfx', 'inventory-restore']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():
                preserve(path, str(path.relative_to(ROOT)))
    preserve(ROOT/'validation/audio-noise-channel/noise-channel/source.sms',
             'retained-fixtures/noise-channel.sms')
    manifest = dict(production_md_sha256=digest,
                    source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                    non_audio_native_sources_unchanged=True, files=items)
    data = (json.dumps(manifest, indent=2)+'\n').encode()
    path = folder/'manifest.json'
    if path.exists():
        assert path.read_bytes() == data
    else:
        with path.open('xb') as stream:
            stream.write(data)
    for item in items:
        assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest() == item['sha256']
    print(len(items), 'immutable source/evidence files archived')


if __name__ == '__main__':
    main()
