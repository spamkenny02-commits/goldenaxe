"""Freeze v0243 source and generated evidence before reclaiming capture space."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    r=json.loads((ROOT/'analysis/heal_terrain_release_v0243_report.json').read_bytes());assert r['passed']
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert digest==r['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==243
    roots=[p for p in (ROOT/'validation').glob('heal-terrain-v0243-*') if p.is_dir()]
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    for pattern in ['analysis/heal_terrain*.json','analysis/heal_terrain_v0243.md','analysis/screen_spell*','validation/heal-terrain-v0243*.log','validation/build-v0243.log','versions/v0243-*/*']:
        paths.update(ROOT.glob(pattern))
    for name in ['README.md','megadrive/src/main.c','megadrive/out/release/symbol.txt','tools/validate_heal_terrain.py','tools/archive_heal_terrain_release.py','analysis/world_next.md','validation/v0243-world-prefix.json']:
        paths.add(ROOT/name)
    prefix=json.loads((ROOT/'validation/v0243-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/heal-terrain-v0243';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=243,full_game_verified=False),roots,cleanup=True)
    recovered=0
    for i in m['compressed'].values():
        encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
    assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==r['source_sha256']
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=243,original_sms_preserved=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/heal_terrain_recovery_v0243_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)

if __name__=='__main__':main()
