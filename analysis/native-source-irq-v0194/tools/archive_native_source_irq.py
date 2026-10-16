"""Freeze native IRQ stage evidence without changing the playable ROM."""
import ast
import hashlib
import json
from actor_reference import ROOT


def main():
    folder=ROOT/'analysis/native-source-irq-v0194';items=[]
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
    baseline=ROOT/'analysis/native-audio-reader-v0194/source-v0194'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['source_irq.c','source_irq.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),path.name
        preserve(path,'source-v0194-irq/'+path.name)
    pending=['archive_native_source_irq','validate_native_source_irq','validate_native_source_irq_68k',
             'validate_native_source_irq_boundaries','validate_source_native_irq_queues'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_source_irq_report.json','native_source_irq_68k_report.json',
                 'native_source_irq_boundaries_report.json','source_native_irq_queues_report.json',
                 'native_source_irq_milestone.md','full_irq_refresh_unit_report.json',
                 'full_irq_unit_report.json','live_full_irq_refresh_report.json',
                 'audio_irq_refresh_unit_report.json','bank_00.asm']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for name in ['native_source_irq_report.json','native_source_irq_68k_report.json',
                 'native_source_irq_boundaries_report.json','source_native_irq_queues_report.json']:
        report=json.loads((ROOT/'analysis'/name).read_text())
        assert report['irq_helper_sha256']==hashlib.sha256((ROOT/'megadrive/src/source_irq.c').read_bytes()).hexdigest()
    for name in ['native-source-irq.log','native-source-irq-68k.log',
                 'native-source-irq-boundaries.log','source-native-irq-queues.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','extension-cases.json','compile.log','source_irq.dll']:
        preserve(ROOT/'validation/native-source-irq'/name,'validation/native-source-irq/'+name)
    for base in sorted((ROOT/'validation/native-source-irq-68k').glob('part-*')):
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    for directory in ['source-irq-queues','full-irq-refresh-unit']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    for relative in ['validation/full-irq-unit/full-irq/source.sms',
                     'validation/audio-irq-refresh-unit/wrapper/source.sms',
                     'validation/audio-irq-refresh-unit/wrapper/auto-results.bin',
                     'validation/audio-irq-refresh-unit/wrapper/pal-results.bin']:
        preserve(ROOT/relative,relative)
    reference=json.loads((ROOT/'analysis/live_full_irq_refresh_report.json').read_text())
    for row in reference['rows']:
        base=ROOT/f"validation/full-irq-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['full-irq-records.bin','full-irq-m1-records.bin','live-envelope-records.bin','audio-irq-events.json']:
            path=base/f"{row['region']}-{suffix}";preserve(path,str(path.relative_to(ROOT)))
    manifest=dict(production_md_sha256=digest,production_ROM_unchanged=True,
                  existing_native_sources_unchanged=True,production_irq_clock_integrated=False,
                  source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable native IRQ source/evidence files archived')


if __name__=='__main__':main()
