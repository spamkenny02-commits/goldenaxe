"""Preserve modal-counter evidence before verified generated cleanup."""
import gzip,json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 report=ROOT/'analysis/overview_clock_release_v0273_report.json';before=report.read_bytes();release=json.loads(before);digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert release['passed'] and release['md_sha256']==digest
 roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==273
 roots=[]
 for pattern in ['overview-clock-*','overview-source-close-*','overview-cost-host','world-frame-coherence-v0273','loot-lifetime-v0273*','screen-spell-v0273*']:
  roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
 paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
 for pattern in ['analysis/overview_clock*.json','analysis/overview_clock_v0273.md','analysis/world_overview_assets.json','analysis/world_overview_cost_report.json','analysis/loot_lifetime_v0273*.json','analysis/screen_spell_v0273*.json','analysis/world_frame_coherence_v0273*.json','validation/overview-clock*.log','validation/overview-source-close*.log','validation/build-v027[23]*.log']:
  paths.update(p for p in ROOT.glob(pattern) if p.is_file())
 for name in ['README.md','analysis/world_next.md','validation/v0273-world-prefix.json','validation/overview-clock-baseline271-symbol.txt','megadrive/src/main.c','megadrive/src/world_overview.inc','megadrive/src/world_overview_assets.inc','megadrive/out/release/symbol.txt','tools/validate_overview_clock.py','tools/summarize_overview_clock_release.py','tools/archive_overview_clock_release.py','tools/generate_world_overview.py','tools/world_overview_cost.py','tools/validate_world_overview_cost.py','tools/profile_world_overview_source.py']:
  paths.add(ROOT/name)
 for e in json.loads((ROOT/'versions/index.json').read_bytes()):
  if 272<=e['version']<=273:paths.update((ROOT/'versions'/e['rom']).parent.iterdir())
 prefix=json.loads((ROOT/'validation/v0273-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 out=ROOT/'analysis/overview-clock-v0273';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=273,prior_cost_capture_manifest_sha256=sha((ROOT/'analysis/world-overview-pacing-v0271/manifest.json').read_bytes()),full_game_verified=False),roots,cleanup=True)
 recovered=0
 for i in m['compressed'].values():
  encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
 subprocess.run([sys.executable,'tools/summarize_overview_clock_release.py'],cwd=ROOT,check=True);assert report.read_bytes()==before
 assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==release['source_sha256']
 removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=273,original_sms_preserved=True,release_identical_after_recovery=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
 (ROOT/'analysis/overview_clock_recovery_v0273_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
