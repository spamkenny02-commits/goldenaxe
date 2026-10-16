"""Freeze v0192 tonal composition sources and source/native validation evidence."""
import ast
import hashlib
import json
from actor_reference import ROOT


def main():
    folder=ROOT/'analysis/native-audio-tone-v0192';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['version']==192)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-noise-v0191/source-v0191'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['sound.inc','source_audio_tone.c','source_audio_tone.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),path.name
        preserve(path,'source-v0192/'+path.name)
    preserve(baseline/'sound.inc','source-v0191/sound.inc')
    pending=['archive_native_audio_tone','validate_native_audio_tone','validate_native_audio_tone_68k',
             'validate_native_audio_tone_rejection','validate_source_native_tone',
             'validate_production_audio_tone','validate_production_audio_sequence',
             'validate_production_audio_noise','validate_production_audio_de',
             'validate_production_audio_priority','validate_music','validate_sfx',
             'validate_music_fade_dispatch','validate_start_menu_audio',
             'validate_start_menu_sfx','validate_inventory_restore'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_tone_report.json','native_audio_tone_68k_report.json',
                 'native_audio_tone_rejection_report.json','source_native_tone_report.json',
                 'audio_tone_channel_cost_report.json','audio_tone_channel_refresh_report.json',
                 'native_audio_tone_milestone.md']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-tone.log','native-audio-tone-68k.log','native-audio-tone-rejection.log',
                 'source-native-tone.log','build-v0192.log','production-audio-tone-v0192.log',
                 'production-audio-sequence-v0192.log','production-audio-noise-v0192.log',
                 'production-audio-de-v0192.log','production-audio-priority-auto-v0192.log',
                 'production-audio-priority-pal-v0192.log','music-v0192.log','sfx-v0192.log',
                 'music-fade-v0192.log','start-menu-v0192.log','start-menu-sfx-v0192.log',
                 'inventory-restore-v0192.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','extension-cases.json','compile.log','source_audio_tone.dll']:
        preserve(ROOT/'validation/native-audio-tone'/name,'validation/native-audio-tone/'+name)
    for base in sorted((ROOT/'validation/native-audio-tone-68k').glob('part-*')):
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    for directory in ['audio-tone-extensions','production-audio-tone','production-audio-sequence',
                      'production-audio-noise','production-audio-de','production-audio-priority',
                      'start-menu-sfx','inventory-restore']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    retained=ROOT/'validation/audio-tone-channel/tone-channel/source.sms'
    reference=json.loads((ROOT/'analysis/audio_tone_channel_refresh_report.json').read_text())
    assert hashlib.sha256(retained.read_bytes()).hexdigest()==reference['fixture_sha256']
    preserve(retained,'retained-fixtures/tone-channel.sms')
    manifest=dict(production_md_sha256=digest,
                  source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  non_audio_native_sources_unchanged=True,files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived')


if __name__=='__main__':main()
