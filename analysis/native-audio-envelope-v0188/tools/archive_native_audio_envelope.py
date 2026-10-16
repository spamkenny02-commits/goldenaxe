"""Freeze v0188 envelope code, source basis, DE observers, and release evidence."""
import ast,hashlib,json,re,subprocess
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-audio-envelope-v0188';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8')) if e['version']==188)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-priority-v0187/source-v0187'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['sound.inc','intro_data.c','source_audio_envelope.c','source_audio_envelope.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),('unexpected native change',path.name)
        preserve(path,'source-v0188/'+path.name)
    def arrays(path):
        return {name:bytes(int(v,16) for v in re.findall(r'0x([0-9a-fA-F]+)',body))
                for name,body in re.findall(r'const u8 (\w+)\[\] = \{(.*?)\};',path.read_text(),re.S)}
    old=arrays(baseline/'intro_data.c');new=arrays(ROOT/'megadrive/src/intro_data.c');assert old.keys()==new.keys()
    for name in old:
        if name=='sound_low_rom':assert new[name]==(ROOT/'input/original.sms').read_bytes()[:32768] and new[name][:len(old[name])]==old[name]
        else:assert old[name]==new[name],('asset changed',name)
    for name in ['sound.inc','intro_data.c']:preserve(baseline/name,'source-v0187-'+name)
    pending=['validate_native_audio_envelope','validate_native_audio_envelope_68k',
             'validate_production_audio_envelope','validate_production_audio_de','build_live_reader_refresh_core',
             'validate_production_audio_priority','validate_music','validate_sfx','validate_music_fade_dispatch',
             'validate_start_menu_audio','validate_start_menu_sfx','extract_intro','archive_native_audio_envelope'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_envelope_report.json','native_audio_envelope_68k_report.json','native_audio_envelope_milestone.md',
                 'audio_adsr_refresh_report.json','audio_table_envelope_refresh_report.json','intro_assets.json']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    preserve(ROOT/'analysis/audio-reader-refresh-live-v0183/z80-live-reader-refresh.txt','source-observer/z80-live-reader-refresh.txt')
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-envelope.log','native-audio-envelope-68k.log','build-v0188.log',
                 'production-audio-envelope-v0188.log','production-audio-de-v0188.log',
                 'production-audio-priority-auto-v0188.log','production-audio-priority-pal-v0188.log',
                 'music-v0188.log','sfx-v0188.log','music-fade-v0188.log','start-menu-v0188.log','start-menu-sfx-v0188.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','compile.log','source_audio_envelope.dll']:
        preserve(ROOT/'validation/native-audio-envelope'/name,'validation/native-audio-envelope/'+name)
    base=ROOT/'validation/native-audio-envelope-68k'
    for path in sorted((base/'src').iterdir()):preserve(path,'validation/native-audio-envelope-68k/src/'+path.name)
    for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
        preserve(base/name,'validation/native-audio-envelope-68k/'+name)
    for directory in ['production-audio-de','production-audio-envelope','production-audio-priority']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    manifest=dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  assets_unchanged_except_expanded_fixed_ROM=True,files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived; original assets audited')

if __name__=='__main__':main()
