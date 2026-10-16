"""Freeze v0190 source, retained/new original-instruction fixtures and ROM evidence."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
    folder=ROOT/'analysis/native-audio-sequence-v0190';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8')) if e['version']==190)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-pitch-v0189/source-v0189'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['sound.inc','source_audio_sequence.c','source_audio_sequence.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),('unexpected native change',path.name)
        preserve(path,'source-v0190/'+path.name)
    preserve(baseline/'sound.inc','source-v0189-sound.inc')
    pending=['validate_native_audio_sequence','validate_native_audio_sequence_68k','validate_source_native_sequence_extensions',
             'validate_audio_sequence_rejection','validate_production_audio_sequence','validate_inventory_restore',
             'validate_production_audio_de','validate_production_audio_priority','validate_music','validate_sfx',
             'validate_music_fade_dispatch','validate_start_menu_audio','validate_start_menu_sfx','archive_native_audio_sequence'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_sequence_report.json','native_audio_sequence_68k_report.json','source_native_sequence_extensions_report.json',
                 'audio_sequence_rejection_report.json','native_audio_sequence_milestone.md']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for kind in ['notes','commands','termination','ownership']:
        preserve(ROOT/f'analysis/audio_note_{kind}_refresh_report.json',f'analysis/audio_note_{kind}_refresh_report.json')
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-sequence.log','native-audio-sequence-68k.log','source-native-sequence-extensions.log',
                 'audio-sequence-rejection.log','build-v0190.log','production-audio-sequence-v0190.log','inventory-restore-v0190.log',
                 'production-audio-de-v0190.log','production-audio-priority-auto-v0190.log','production-audio-priority-pal-v0190.log',
                 'music-v0190.log','sfx-v0190.log','music-fade-v0190.log','start-menu-v0190.log','start-menu-sfx-v0190.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','extension-cases.json','compile.log','source_audio_sequence.dll']:
        preserve(ROOT/'validation/native-audio-sequence'/name,'validation/native-audio-sequence/'+name)
    for base in sorted((ROOT/'validation/native-audio-sequence-68k').glob('part-*')):
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    base=ROOT/'validation/native-audio-sequence-rejection-68k'
    for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
    for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
        preserve(base/name,str((base/name).relative_to(ROOT)))
    for directory in ['audio-sequence-extensions','production-audio-sequence','production-audio-de','production-audio-priority']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    # Preserve original retained ROMs used by the host/kernel oracle, without
    # duplicating every mutable historical validation directory.
    data=json.loads((ROOT/'validation/native-audio-sequence/cases.json').read_text())
    for suite in data['suites']:preserve(ROOT/suite['fixture'],'retained-fixtures/'+suite['kind']+'.sms')
    manifest=dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                  non_audio_native_sources_unchanged=True,files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable source/evidence files archived')

if __name__=='__main__':main()
