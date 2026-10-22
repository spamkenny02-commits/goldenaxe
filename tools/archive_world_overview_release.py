"""Freeze overview evidence before removing only verified generated captures."""
import json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
    release=ROOT/'analysis/world_overview_release_v0240_report.json';before=release.read_bytes();r=json.loads(before);digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert r['passed'] and r['md_sha256']==digest
    roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==240
    original=sha((ROOT/'input/original.sms').read_bytes());assert original==r['source_sha256']
    roots=[]
    for pattern in ['world-overview-v023*','world-overview-v0240*']:
        roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
    paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
    names=['README.md','build.ps1','megadrive/src/main.c','megadrive/src/world_overview.inc','megadrive/src/world_overview_assets.inc','megadrive/out/release/symbol.txt','tools/generate_world_overview.py','tools/validate_world_overview.py','tools/summarize_world_overview_release.py','tools/archive_world_overview_release.py','analysis/world_next.md','validation/v0240-world-prefix.json','validation/v0239-world_overview.inc']
    paths.update(ROOT/n for n in names)
    for pattern in ['analysis/world_overview*.json','analysis/world_overview_v0240.md','validation/world-overview-v02*.log','validation/build-v023[6789]*.log','validation/build-v0240*.log']:paths.update(ROOT.glob(pattern))
    entries=json.loads((ROOT/'versions/index.json').read_bytes())
    for entry in entries:
        if 236<=entry['version']<=240:paths.update((ROOT/'versions'/entry['rom']).parent.iterdir())
    prefix=json.loads((ROOT/'validation/v0240-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
    out=ROOT/'analysis/world-overview-v0240';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=240,full_game_verified=False),roots,cleanup=True)
    subprocess.run([sys.executable,'tools/summarize_world_overview_release.py'],cwd=ROOT,check=True)
    assert release.read_bytes()==before and all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==original
    removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=240,original_sms_preserved=True,release_report_identical_after_recovery=True,restored_return_final_ram_bytes=12*73728,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    (ROOT/'analysis/world_overview_recovery_v0240_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
