"""Freeze v0186 native source, component oracles, and actual ROM evidence."""
import ast,hashlib,json,subprocess
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-audio-dispatch-v0186';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8')) if e['version']==186)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if path.is_file():preserve(path,'source-v0186/'+path.name)
    pending=['validate_native_audio_dispatch','validate_native_audio_dispatch_68k',
             'validate_production_audio_dispatch','validate_music','validate_sfx',
             'validate_music_fade_dispatch','validate_start_menu_audio','validate_start_menu_sfx',
             'archive_native_audio_dispatch'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_dispatch_report.json','native_audio_dispatch_68k_report.json','native_audio_dispatch_milestone.md']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for item in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/item['file'],'reports/'+item['file'])
    for name in ['native-audio-dispatch.log','native-audio-dispatch-68k.log','build-v0186.log',
                 'production-audio-dispatch-v0186.log','music-v0186.log','sfx-v0186.log',
                 'music-fade-v0186.log','start-menu-v0186.log','start-menu-sfx-v0186.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','compile.log','source_audio_dispatch.dll']:
        preserve(ROOT/'validation/native-audio-dispatch'/name,'validation/native-audio-dispatch/'+name)
    base=ROOT/'validation/native-audio-dispatch-68k'
    for path in sorted((base/'src').iterdir()):preserve(path,'validation/native-audio-dispatch-68k/src/'+path.name)
    for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
        preserve(base/name,'validation/native-audio-dispatch-68k/'+name)
    for path in sorted((ROOT/'validation/production-audio-dispatch').rglob('*')):
        if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    # Preserve the exact preceding production caller for review without relying
    # on mutable working files. The commit is the already-versioned v0185.
    old=subprocess.run(['git','show','bbd4427:megadrive/src/sound.inc'],cwd=ROOT,capture_output=True,check=True).stdout
    path=folder/'source-v0185-sound.inc'
    if path.exists():assert path.read_bytes()==old
    else:
        with path.open('xb') as stream:stream.write(old)
    items.append(dict(path=path.name,sha256=hashlib.sha256(old).hexdigest()))
    manifest=dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived')

if __name__=='__main__':main()
