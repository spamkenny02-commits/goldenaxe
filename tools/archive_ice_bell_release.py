"""Preserve bell evidence losslessly, then remove only archived generated captures."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    r=json.loads((ROOT/'analysis/ice_bell_release_v0242_report.json').read_bytes());assert r['passed']
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest==r['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==242
    roots=[p for p in (ROOT/'validation').glob('ice-bell-v024*') if p.is_dir()]
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    for pattern in ['analysis/ice_bell*.json','analysis/ice_bell_v0242.md','validation/ice-bell-v024*.log','validation/build-v024[12].log','versions/v024[12]-*/*']:
        paths.update(ROOT.glob(pattern))
    for name in ['README.md','build.ps1','megadrive/src/main.c','megadrive/src/ice_bell.inc','megadrive/src/ice_bell_assets.inc','megadrive/out/release/symbol.txt','tools/generate_ice_bell.py','tools/validate_ice_bell.py','tools/summarize_ice_bell_release.py','tools/archive_ice_bell_release.py','analysis/world_next.md','validation/v0242-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/v0242-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/ice-bell-v0242';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=242,full_game_verified=False),roots,cleanup=True)
    restored=0
    for name,i in m['compressed'].items():
        encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];restored+=len(raw)
    assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==r['source_sha256']
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=242,original_sms_preserved=True,recovered_bytes_verified=restored,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/ice_bell_recovery_v0242_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)

if __name__=='__main__':main()
