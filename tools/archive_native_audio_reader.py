"""Freeze v0194 full-reader evidence and the failed v0193 integration diagnostic."""
import ast
import hashlib
import json
from actor_reference import ROOT


def main():
    folder=ROOT/'analysis/native-audio-reader-v0194';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['version']==194)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-audio-tone-v0192/source-v0192'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['sound.inc','source_audio_reader.c','source_audio_reader.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),path.name
        preserve(path,'source-v0194/'+path.name)
    preserve(baseline/'sound.inc','source-v0192/sound.inc')
    pending=['archive_native_audio_reader','validate_native_audio_reader','validate_native_audio_reader_68k',
             'validate_native_audio_reader_rejection','validate_source_native_reader',
             'validate_production_audio_reader','validate_production_audio_tone',
             'validate_production_audio_sequence','validate_production_audio_noise',
             'validate_production_audio_de','validate_production_audio_priority',
             'validate_music','validate_sfx','validate_music_fade_dispatch',
             'validate_start_menu_audio','validate_start_menu_sfx','validate_inventory_restore'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_audio_reader_report.json','native_audio_reader_68k_report.json',
                 'native_audio_reader_rejection_report.json','source_native_reader_report.json',
                 'audio_reader_gates_cost_report.json','audio_reader_refresh_report.json',
                 'live_audio_reader_refresh_report.json','reader_buffer_boot_diagnostic.json',
                 'native_audio_reader_milestone.md']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for report in entry['reports']:
        path=ROOT/'versions'/entry['rom'];preserve(path.parent/report['file'],'reports/'+report['file'])
    for name in ['native-audio-reader.log','native-audio-reader-68k.log','native-audio-reader-rejection.log',
                 'source-native-reader.log','build-v0193.log','build-v0194.log',
                 'production-audio-reader-v0193.log','music-v0193.log','sfx-v0193.log',
                 'production-audio-reader-v0194.log','production-audio-tone-v0194.log',
                 'production-audio-sequence-v0194.log','production-audio-noise-v0194.log',
                 'production-audio-de-v0194.log','production-audio-priority-auto-v0194.log',
                 'production-audio-priority-pal-v0194.log','music-v0194.log','sfx-v0194.log',
                 'music-fade-v0194.log','start-menu-v0194.log','start-menu-sfx-v0194.log',
                 'inventory-restore-v0194.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','extension-cases.json','compile.log','source_audio_reader.dll']:
        preserve(ROOT/'validation/native-audio-reader'/name,'validation/native-audio-reader/'+name)
    for base in sorted((ROOT/'validation/native-audio-reader-68k').glob('part-*')):
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    for directory in ['audio-reader-extensions','production-audio-reader','production-audio-tone',
                      'production-audio-sequence','production-audio-noise','production-audio-de',
                      'production-audio-priority','start-menu-sfx','reader-boot-diagnostic']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    for base in sorted((ROOT/'validation').glob('inventory-restore-*-*-*')):
        if not base.is_dir():continue
        for path in sorted(base.rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    retained=ROOT/'validation/audio-reader-gates/gates/source.sms'
    reference=json.loads((ROOT/'analysis/audio_reader_refresh_report.json').read_text())
    assert hashlib.sha256(retained.read_bytes()).hexdigest()==reference['fixture_sha256']
    preserve(retained,'retained-fixtures/reader-gates.sms')
    reference=json.loads((ROOT/'analysis/live_audio_reader_refresh_report.json').read_text())
    for row in reference['rows']:
        base=ROOT/f"validation/reader-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        for suffix,key in [('live-envelope-records.bin','state_cost_sha256'),('live-envelope-m1-records.bin','M1_R_sha256')]:
            path=base/f"{row['region']}-{suffix}"
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row[key]
            preserve(path,str(path.relative_to(ROOT)))
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
