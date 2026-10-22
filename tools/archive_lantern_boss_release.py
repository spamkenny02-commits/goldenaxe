"""Archive the completed lantern/boss-latch release before generated-file cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    report=json.loads((ROOT/'analysis/lantern_release_v0232_report.json').read_bytes());digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert report['passed'] and digest==report['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==232
    original=sha((ROOT/'input/original.sms').read_bytes());assert original==report['source_sha256']
    roots=[]
    for pattern in ['lantern-v0231-*','lantern-v0232-*','inventory-acceptance-v0232*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    roots.extend(ROOT/f'validation/natural-dungeon-route/{name}' for name in ['md-v0232','md-pal-v0232'])
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    names=['README.md','megadrive/src/main.c','megadrive/out/release/symbol.txt','tools/validate_lantern_gameplay.py','tools/archive_lantern_boss_release.py','analysis/world_next.md','validation/v0232-world-prefix.json']
    paths.update(ROOT/n for n in names)
    for pattern in ['analysis/lantern*v0232*.json','analysis/lantern_v0231*_report.json','analysis/lantern_v0232.md','analysis/inventory_acceptance_v0232*.json','validation/*v0232*.log','validation/lantern-v0229.log']:paths.update(ROOT.glob(pattern))
    paths.update((ROOT/'versions/v0232-786d954c').iterdir())
    paths.update((ROOT/'versions/v0231-390ada84').iterdir())
    prefix=json.loads((ROOT/'validation/v0232-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/lantern-v0232';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=232,full_game_verified=False),roots,cleanup=True)
    recovered=0
    for case in ['v0232','v0232-pal','v0232-boss','v0232-boss-pal','v0232-boss-death','v0232-boss-death-pal']:
        for tag in ['sms','md']:
            path=f'validation/lantern-{case}-{tag}/ram_04740.bin';i=m['compressed'][path];stored=(out/i['stored']).read_bytes();assert sha(stored)==i['stored_sha256'];raw=gzip.decompress(stored);assert sha(raw)==i['raw_sha256'];recovered+=len(raw)
    assert recovered==442368 and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=232,original_sms_preserved=True,final_ram_bytes_recovered=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/lantern_recovery_v0232_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
