"""Freeze native wait/clock/dynamicIRQ proof while retaining playable v0194."""
import ast
import hashlib
import json
from actor_reference import ROOT
from validate_native_source_wait import MODULES


def main():
    folder=ROOT/'analysis/native-source-wait-v0194';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['version']==194)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-source-irq-v0194/source-v0194-irq'
    additions=['source_irq_context.c','source_irq_context.h','source_wait.c','source_wait.h']
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in additions+['source_clock.c','source_clock.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),path.name
        preserve(path,'source-v0194-wait/'+path.name)
    assert (ROOT/'megadrive/src/source_clock.c').read_text().startswith((baseline/'source_clock.c').read_text())
    for name in ['source_clock.c','source_clock.h']:preserve(baseline/name,'source-v0194-irq/'+name)
    pending=['archive_native_source_wait','validate_native_source_wait','validate_native_source_wait_unit',
             'validate_native_source_wait_68k','audit_native_irq_entries','validate_native_clock_repeat',
             'validate_native_irq_context_boundaries'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_source_wait_report.json','native_source_wait_unit_report.json','native_source_wait_68k_report.json',
                 'native_irq_entry_report.json','native_clock_repeat_report.json','native_irq_context_boundaries_report.json',
                 'native_source_wait_milestone.md','wait_refresh_report.json','wait_refresh_unit_report.json',
                 'wait_raster_unit_report.json','wait_raster_pal_latched_unit_report.json','bank_00.asm']:
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    for name in ['native_source_wait_report.json','native_source_wait_unit_report.json','native_source_wait_68k_report.json']:
        report=json.loads((ROOT/'analysis'/name).read_text())
        for module in MODULES:assert report['helper_sha256'][module]==hashlib.sha256((ROOT/'megadrive/src'/f'{module}.c').read_bytes()).hexdigest()
    report=json.loads((ROOT/'analysis/native_source_wait_68k_report.json').read_text())
    assert report['cases']==19881 and all(r['done']==1 and r['failures']==0 for r in report['results'])
    for name in ['native-source-wait.log','native-source-wait-unit.log','native-source-wait-68k.log',
                 'native-irq-entries.log','native-clock-repeat.log','native-irq-context-boundaries.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['cases.json','extension-cases.json','wrapper.c','compile.log','source_wait.dll']:
        preserve(ROOT/'validation/native-source-wait'/name,'validation/native-source-wait/'+name)
    for directory,dll in [('native-clock-repeat','clock_repeat.dll'),('native-irq-context-boundaries','context.dll')]:
        for name in ['wrapper.c','compile.log',dll]:preserve(ROOT/'validation'/directory/name,f'validation/{directory}/{name}')
    for base in sorted((ROOT/'validation/native-source-wait-68k').glob('part-*')):
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    for path in sorted((ROOT/'validation/native-source-wait-unit').rglob('*')):
        if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    for relative in ['validation/wait-raster-unit/wait/source.sms','validation/wait-raster-unit-pal/wait/source.sms']:
        preserve(ROOT/relative,relative)
    reference=json.loads((ROOT/'analysis/wait_refresh_report.json').read_text())
    for row in reference['rows']:
        relative=f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['foreground-phase-records.bin','foreground-m1-records.bin','save-wait-records.bin','audio-irq-events.json']:
            path=ROOT/relative/f"{row['region']}-{suffix}";preserve(path,str(path.relative_to(ROOT)))
        relative=f"validation/full-irq-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['full-irq-records.bin','full-irq-m1-records.bin']:
            path=ROOT/'analysis/full-irq-refresh-research-v0183'/relative/f"{row['region']}-{suffix}"
            preserve(path,'reference/'+relative+'/'+path.name)
    manifest=dict(production_md_sha256=digest,production_ROM_unchanged=True,existing_game_sources_unchanged=True,
                  existing_clock_functions_unchanged=True,production_clock_integrated=False,
                  source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable native wait/clock/dynamicIRQ source/evidence files archived')


if __name__=='__main__':main()
