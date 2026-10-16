"""Freeze v0189 native pitch/memory, source instruction proof, and ROM checks."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-audio-pitch-v0189';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8')) if e['version']==189)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-envelope-v0188/source-v0188'
    changes=['sound.inc','source_audio_envelope.c','source_audio_pitch.c','source_audio_pitch.h','source_audio_memory.c','source_audio_memory.h']
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in changes:assert path.read_bytes()==(baseline/path.name).read_bytes(),('unexpected native change',path.name)
        preserve(path,'source-v0189/'+path.name)
    for name in ['sound.inc','source_audio_envelope.c']:preserve(baseline/name,'source-v0188-'+name)
    pending=['validate_native_audio_pitch','validate_native_audio_pitch_68k','validate_audio_pitch_refresh',
             'validate_native_audio_envelope','validate_native_audio_envelope_68k',
             'validate_production_audio_pitch','validate_production_audio_envelope','validate_production_audio_de',
             'validate_production_audio_priority','validate_music','validate_sfx','validate_music_fade_dispatch',
             'validate_start_menu_audio','validate_start_menu_sfx','archive_native_audio_pitch'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_pitch_report.json','native_audio_pitch_68k_report.json','native_audio_pitch_milestone.md',
                 'audio_pitch_refresh_report.json','native_audio_envelope_report.json','native_audio_envelope_68k_report.json']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-pitch.log','native-audio-pitch-68k.log','audio-pitch-refresh-v0189.log',
                 'native-audio-envelope-v0189.log','native-audio-envelope-68k-v0189.log','build-v0189.log',
                 'production-audio-pitch-v0189.log','production-audio-envelope-v0189.log','production-audio-de-v0189.log',
                 'production-audio-priority-auto-v0189.log','production-audio-priority-pal-v0189.log',
                 'music-v0189.log','sfx-v0189.log','music-fade-v0189.log','start-menu-v0189.log','start-menu-sfx-v0189.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for kind in ['pitch','envelope']:
        for name in ['cases.json','compile.log',f'source_audio_{kind}.dll']:
            preserve(ROOT/f'validation/native-audio-{kind}'/name,f'validation/native-audio-{kind}/'+name)
        base=ROOT/f'validation/native-audio-{kind}-68k'
        for path in sorted((base/'src').iterdir()):preserve(path,f'validation/native-audio-{kind}-68k/src/'+path.name)
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,f'validation/native-audio-{kind}-68k/'+name)
    base=ROOT/'validation/audio-pitch-refresh/pitch'
    for name in ['source.sms','auto-results.bin','pal-results.bin','auto/capture.json','pal/capture.json']:
        preserve(base/name,'validation/audio-pitch-refresh/pitch/'+name)
    for directory in ['production-audio-pitch','production-audio-envelope','production-audio-de','production-audio-priority']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    manifest=dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  non_audio_native_sources_unchanged=True,files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived; non-audio sources unchanged')

if __name__=='__main__':main()
