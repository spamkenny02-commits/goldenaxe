"""Freeze full-wait caller/restore/chain proofs without replacing playable v0194."""
import ast
import hashlib
import json
from actor_reference import ROOT
from native_wait_return_support import MODULES


def main():
    folder=ROOT/'analysis/native-wait-return-v0194';items=[]
    def preserve(path,name):
        data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
        else:
            with target.open('xb') as stream:stream.write(data)
        items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['version']==194)
    assert digest==entry['sha256'] and entry['validation']=='targeted_checks_passed'
    baseline=ROOT/'analysis/native-source-wait-v0194/source-v0194-wait'
    for path in sorted((ROOT/'megadrive/src').iterdir()):
        if not path.is_file():continue
        if path.name not in ['source_wait_restore.c','source_wait_restore.h']:
            assert path.read_bytes()==(baseline/path.name).read_bytes(),path.name
        preserve(path,'source-v0194-return/'+path.name)
    pending=['archive_native_wait_return','build_wait_return_core','native_wait_return_support',
             'validate_native_wait_return_unit','validate_native_wait_restore_boundaries',
             'validate_native_wait_return_live','validate_native_wait_return_68k',
             'validate_native_wait_chains','validate_native_wait_chain_68k'];seen=set()
    while pending:
        name=pending.pop();path=ROOT/'tools'/f'{name}.py'
        if name in seen or not path.exists():continue
        seen.add(name);preserve(path,'tools/'+path.name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
            elif isinstance(node,ast.Import):pending.extend(a.name.split('.')[0] for a in node.names)
    for name in ['native_wait_return_unit_report.json','native_wait_restore_boundaries_report.json',
                 'native_wait_return_live_report.json','native_wait_return_68k_report.json',
                 'native_wait_chain_report.json','native_wait_chain_68k_report.json']:
        report=json.loads((ROOT/'analysis'/name).read_text())
        for module in MODULES:assert report['helper_sha256'][module]==hashlib.sha256((ROOT/'megadrive/src'/f'{module}.c').read_bytes()).hexdigest()
        preserve(ROOT/'analysis'/name,'analysis/'+name)
    report=json.loads((ROOT/'analysis/native_wait_return_68k_report.json').read_text())
    assert report['cases']==38349 and len(report['results'])==40 and all(r['done']==1 and r['failures']==0 for r in report['results'])
    report=json.loads((ROOT/'analysis/native_wait_chain_68k_report.json').read_text())
    assert report['chains']==816 and all(r['done']==1 and r['failures']==0 for r in report['results'])
    preserve(ROOT/'analysis/native_wait_return_milestone.md','analysis/native_wait_return_milestone.md')
    preserve(ROOT/'analysis/wait-return-observer-v0194/z80-wait-return-v2.txt','observer/z80-wait-return-v2.txt')
    preserve(ROOT/'analysis/wait-refresh-v0183/z80-wait-refresh.txt','observer/base-z80-wait-refresh.txt')
    preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitcomplete_libretro.dll','observer/genesis_plus_gx_waitcomplete_libretro.dll')
    for name in ['build-wait-return-core-v2.log','wait-return-core-build.log','native-wait-return-unit.log',
                 'native-wait-restore-boundaries.log','native-wait-restore-pal-latched.log',
                 'native-wait-return-live.log','native-wait-return-68k.log','native-wait-chains.log','native-wait-chain-68k.log']:
        preserve(ROOT/'validation'/name,'logs/'+name)
    for name in ['unit-cases.json','restore-cases.json','live-cases.json','chain-cases.json','wrapper.c','compile.log','wait_return.dll']:
        preserve(ROOT/'validation/native-wait-return'/name,'validation/native-wait-return/'+name)
    bases=sorted((ROOT/'validation/native-wait-return-68k').glob('part-*'))+[ROOT/'validation/native-wait-chain-68k']
    for base in bases:
        for path in sorted((base/'src').iterdir()):preserve(path,str(path.relative_to(ROOT)))
        for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:
            preserve(base/name,str((base/name).relative_to(ROOT)))
    for directory in ['wait-return-unit','wait-restore-boundaries','wait-restore-boundaries-pal','wait-return-live']:
        for path in sorted((ROOT/'validation'/directory).rglob('*')):
            if path.is_file():preserve(path,str(path.relative_to(ROOT)))
    for relative in ['validation/wait-raster-unit/wait/source.sms','validation/wait-raster-unit-pal/wait/source.sms']:
        preserve(ROOT/relative,relative)
    for path in sorted((ROOT/'validation/native-source-wait-unit').rglob('*')):
        if path.is_file() and path.name in ['pairs.bin','m1.bin']:preserve(path,'reference/'+str(path.relative_to(ROOT)))
    reference=json.loads((ROOT/'analysis/wait_refresh_report.json').read_text())
    preserve(ROOT/'analysis/wait_refresh_report.json','reference/wait_refresh_report.json')
    for row in reference['rows']:
        relative=f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}"
        for suffix in ['cycle-events.json','foreground-phase-records.bin','foreground-m1-records.bin','save-wait-records.bin']:
            path=ROOT/relative/f"{row['region']}-{suffix}";preserve(path,'reference/'+str(path.relative_to(ROOT)))
        path=ROOT/relative/f"captures-{row['region']}-sms/capture.json";preserve(path,'reference/'+str(path.relative_to(ROOT)))
    manifest=dict(production_md_sha256=digest,production_ROM_unchanged=True,existing_native_sources_unchanged=True,
                  production_clock_integrated=False,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items)
    data=(json.dumps(manifest,indent=2)+'\n').encode();path=folder/'manifest.json'
    if path.exists():assert path.read_bytes()==data
    else:
        with path.open('xb') as stream:stream.write(data)
    for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
    print(len(items),'immutable complete-wait/restore/chain evidence files archived')


if __name__=='__main__':main()
