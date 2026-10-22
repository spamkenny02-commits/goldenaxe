"""Freeze v0229 evidence with hash readback before removing generated captures."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    report=json.loads((ROOT/'analysis/inventory_release_v0229_report.json').read_bytes())
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert report['passed'] and digest==report['md_sha256']
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==229
    original=sha((ROOT/'input/original.sms').read_bytes());assert original==report['source_sha256']
    roots=[]
    for pattern in ['inventory-acceptance-v022*','natural-axe-v0229-*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    roots.extend(ROOT/f'validation/natural-dungeon-combat/{tag}-auto-{trial}' for tag in ['sms','md'] for trial in [26,27])
    roots.append(ROOT/'validation/natural-dungeon-route/md-v0229')
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    names=['README.md','megadrive/src/main.c','megadrive/out/release/symbol.txt','tools/natural_dungeon_combat.py','tools/natural_axe_inventory.py','tools/validate_inventory_acceptance.py','tools/archive_inventory_release.py','analysis/world_next.md','validation/v0229-world-prefix.json']
    paths.update(ROOT/n for n in names)
    for pattern in ['analysis/inventory*v022*.json','analysis/inventory_v0229.md','validation/*v0229*.log','validation/natural-item-*-2[67].log']:
        paths.update(ROOT.glob(pattern))
    paths.update((ROOT/'versions/v0229-a9ae2d0a').iterdir())
    prefix=json.loads((ROOT/'validation/v0229-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/inventory-v0229'
    m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=229,full_game_verified=False),roots,cleanup=True)
    # Independently recover the final normal-play RAM captures after cleanup.
    recovered=0
    for tag in ['sms','md']:
        folder=ROOT/f'validation/natural-axe-v0229-{tag}';capture=json.loads((folder/'capture.json').read_bytes());end=capture['frames']
        path=folder/f'ram_{end:05}.bin';i=m['compressed'][path.relative_to(ROOT).as_posix()]
        stored=(out/i['stored']).read_bytes();assert sha(stored)==i['stored_sha256'];raw=gzip.decompress(stored);assert sha(raw)==i['raw_sha256'];recovered+=len(raw)
    assert recovered==73728 and all(sha(p.read_bytes())==h for p,h in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(x['bytes'] for x in m['removed_verified_generated'])
    result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=229,original_sms_preserved=True,normal_play_final_ram_bytes_recovered=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/inventory_recovery_v0229_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
