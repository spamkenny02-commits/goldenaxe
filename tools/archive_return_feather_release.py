"""Freeze feather evidence, verify recovery, preserve all numbered ROMs."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    report=json.loads((ROOT/'analysis/return_feather_release_v0235_report.json').read_bytes());digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert report['passed'] and report['md_sha256']==digest
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==235
    original=sha((ROOT/'input/original.sms').read_bytes());assert original==report['source_sha256']
    roots=[]
    for pattern in ['return-feather-v023*','feather-purchase-v023*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    names=['README.md','megadrive/src/main.c','megadrive/src/return_feather.inc','megadrive/out/release/symbol.txt','tools/validate_return_feather.py','tools/play_feather_purchase.py','tools/archive_return_feather_release.py','analysis/world_next.md','validation/v0235-world-prefix.json']
    paths.update(ROOT/n for n in names)
    for pattern in ['analysis/return_feather*.json','analysis/return_feather_v0235.md','validation/return-feather-v023*.log','validation/feather-purchase-v023*.log','validation/build-v023[345].log']:paths.update(ROOT.glob(pattern))
    for name in ['v0233-bf93267a','v0234-fb0cea5e','v0235-7c9f6750']:paths.update((ROOT/'versions'/name).iterdir())
    prefix=json.loads((ROOT/'validation/v0235-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/return-feather-v0235';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=235,full_game_verified=False),roots,cleanup=True)
    recovered=0
    names=['v0235','v0235-pal','v0235-town','v0235-town-pal','v0235-hurt','v0235-hurt-pal','v0235-moving','v0235-moving-pal']
    folders=[ROOT/f'validation/return-feather-{name}-{tag}' for name in names for tag in ['sms','md']]
    folders.extend(ROOT/f'validation/feather-purchase-v0235-{tag}' for tag in ['sms','md'])
    for folder in folders:
        c=json.loads((folder/'capture.json').read_bytes());end=3300 if 'return-feather' in folder.name else c['frames'];path=folder/f'ram_{end:05}.bin';i=m['compressed'][path.relative_to(ROOT).as_posix()];stored=(out/i['stored']).read_bytes();assert sha(stored)==i['stored_sha256'];raw=gzip.decompress(stored);assert sha(raw)==i['raw_sha256'];recovered+=len(raw)
    assert recovered==663552 and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=235,original_sms_preserved=True,final_ram_bytes_recovered=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/return_feather_recovery_v0235_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
