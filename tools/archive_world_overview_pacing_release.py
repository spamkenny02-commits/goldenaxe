"""Freeze overview pacing evidence before verified generated capture cleanup."""
import gzip,json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 report=ROOT/'analysis/world_overview_pacing_release_v0271_report.json';before=report.read_bytes();release=json.loads(before);digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert release['passed'] and release['md_sha256']==digest
 roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==271
 roots=[]
 for pattern in ['world-overview-v0271*','overview-source-*','overview-cost-host','world-frame-coherence-v0271','loot-lifetime-v0271*','screen-spell-v0271*']:
  roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
 paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
 for pattern in ['analysis/world_overview*.json','analysis/world_overview_pacing_v0271.md','analysis/world-overview-timing-source/*','analysis/loot_lifetime_v0271*.json','analysis/screen_spell_v0271*.json','analysis/world_frame_coherence_v0271*.json','validation/overview*.log','validation/world-overview-timing-core-build.log','validation/build-v0271*.log']:
  paths.update(p for p in ROOT.glob(pattern) if p.is_file())
 for name in ['README.md','build.ps1','analysis/world_next.md','validation/v0271-world-prefix.json','megadrive/src/main.c','megadrive/src/world_overview.inc','megadrive/src/world_overview_assets.inc','megadrive/src/sound.inc','megadrive/out/release/symbol.txt','tools/generate_world_overview.py','tools/validate_world_overview.py','tools/world_overview_cost.py','tools/validate_world_overview_cost.py','tools/profile_world_overview_source.py','tools/build_world_overview_timing_core.py','tools/summarize_world_overview_pacing_release.py','tools/archive_world_overview_pacing_release.py','tools/ram_plane_loading_cost.py','tools/world_map_loading_cost.py','tools/extract_title.py']:
  paths.add(ROOT/name)
 for e in json.loads((ROOT/'versions/index.json').read_bytes()):
  if e['version']==271:paths.update((ROOT/'versions'/e['rom']).parent.iterdir())
 prefix=json.loads((ROOT/'validation/v0271-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 out=ROOT/'analysis/world-overview-pacing-v0271';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=271,full_game_verified=False),roots,cleanup=True)
 recovered=0
 for i in m['compressed'].values():
  encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
 subprocess.run([sys.executable,'tools/summarize_world_overview_pacing_release.py'],cwd=ROOT,check=True);assert report.read_bytes()==before
 assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==release['source_sha256']
 removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=271,original_sms_preserved=True,release_identical_after_recovery=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
 (ROOT/'analysis/world_overview_pacing_recovery_v0271_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
