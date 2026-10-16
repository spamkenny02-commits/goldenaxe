"""Freeze v0187 priority/restoration source, models, and execution evidence."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-audio-priority-v0187';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8')) if e['version']==187)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-dispatch-v0186/source-v0186'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['sound.inc','source_audio_priority.c','source_audio_priority.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),('unexpected native change',path.name)
        preserve(path,'source-v0187/'+path.name)
    preserve(baseline/'sound.inc','source-v0186-sound.inc')
    pending=['validate_native_audio_priority','validate_native_audio_priority_68k',
             'validate_audio_restore_effect_refresh','validate_production_audio_priority',
             'validate_music','validate_sfx','validate_music_fade_dispatch','validate_start_menu_audio',
             'validate_start_menu_sfx','archive_native_audio_priority'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['audio_priority_effect_cost','audio_priority_effect_refresh']:
        assert (ROOT/'tools'/f'{name}.py').read_bytes()==(ROOT/'analysis/native-audio-dispatch-v0186/tools'/f'{name}.py').read_bytes()
    for name in ['native_audio_priority_report.json','native_audio_priority_68k_report.json',
                 'audio_restore_effect_refresh_report.json','native_audio_priority_milestone.md',
                 'audio_priority_effect_refresh_report.json','audio_priority_effect_cost_report.json']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-priority.log','native-audio-priority-68k.log','audio-restore-effect-refresh.log',
                 'build-v0187.log','production-audio-priority-auto-v0187.log','production-audio-priority-pal-v0187.log',
                 'music-v0187.log','sfx-v0187.log','music-fade-v0187.log','start-menu-v0187.log','start-menu-sfx-v0187.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','compile.log','source_audio_priority.dll']:
        preserve(ROOT/'validation/native-audio-priority'/name,'validation/native-audio-priority/'+name)
    base=ROOT/'validation/native-audio-priority-68k'
    for path in sorted((base/'src').iterdir()):preserve(path,'validation/native-audio-priority-68k/src/'+path.name)
    for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
        preserve(base/name,'validation/native-audio-priority-68k/'+name)
    base=ROOT/'validation/audio-restore-effect-refresh/restore'
    for name in ['source.sms','auto-results.bin','pal-results.bin','auto/capture.json','pal/capture.json']:
        preserve(base/name,'validation/audio-restore-effect-refresh/restore/'+name)
    for path in sorted((ROOT/'validation/production-audio-priority').rglob('*')):
        if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    manifest=dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived')

if __name__=='__main__':main()
