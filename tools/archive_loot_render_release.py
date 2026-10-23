"""Losslessly preserve loot render work before removing generated captures."""
import gzip,json,subprocess,sys
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 report=ROOT/'analysis/loot_render_release_v0270_report.json';before=report.read_bytes();r=json.loads(before);digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());assert r['passed'] and r['md_sha256']==digest
 roms={p:sha(p.read_bytes()) for p in (ROOT/'versions').glob('*/*.bin')};assert len(roms)==270
 roots=[]
 for pattern in ['loot-lifetime-v026[789]*','loot-lifetime-v0270*','loot-pickup-v0270*','sprite-overflow-bands-host','sprite-cache-cursor-host','world-frame-coherence-v0268','world-frame-coherence-v0270','screen-spell-v0270*','ice-bell-v0270*']:
  roots.extend(p for p in (ROOT/'validation').glob(pattern) if p.is_dir())
 paths={p for folder in roots for p in folder.rglob('*') if p.is_file()}
 for pattern in ['analysis/loot_lifetime*.json','analysis/loot_pickup_v0270_report.json','analysis/loot_render*','analysis/sprite_overflow_bands_host_report.json','analysis/sprite_cache_cursor_host_report.json','analysis/screen_spell_v0270*.json','analysis/ice_bell_v0270*.json','analysis/world_frame_coherence_v0268*.json','analysis/world_frame_coherence_v0270*.json','validation/loot*.log','validation/world-frame-coherence-v0268.log','validation/world-frame-coherence-v0270.log','validation/build-v026[89]*.log','validation/build-v0270*.log']:
  paths.update(p for p in ROOT.glob(pattern) if p.is_file())
 for name in ['README.md','analysis/world_next.md','validation/v0270-world-prefix.json','validation/sms-shield-detail/ram_03740.bin','megadrive/src/main.c','megadrive/src/actors.c','megadrive/src/pattern_convert.c','megadrive/out/release/symbol.txt','tools/validate_loot_lifetime.py','tools/validate_loot_pickup_current.py','tools/validate_sprite_overflow_bands.py','tools/validate_sprite_cache_cursor.py','tools/summarize_loot_render_release.py','tools/archive_loot_render_release.py']:
  paths.add(ROOT/name)
 for e in json.loads((ROOT/'versions/index.json').read_bytes()):
  if 268<=e['version']<=270:paths.update((ROOT/'versions'/e['rom']).parent.iterdir())
 prefix=json.loads((ROOT/'validation/v0270-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 out=ROOT/'analysis/loot-render-v0270';m=freeze(ROOT,out,paths,dict(md_sha256=digest,numbered_roms_preserved=270,full_game_verified=False),roots,cleanup=True)
 recovered=0
 for i in m['compressed'].values():
  encoded=(out/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'] and len(raw)==i['raw_bytes'];recovered+=len(raw)
 subprocess.run([sys.executable,'tools/summarize_loot_render_release.py'],cwd=ROOT,check=True);assert report.read_bytes()==before
 assert all(sha(p.read_bytes())==v for p,v in roms.items()) and sha((ROOT/'input/original.sms').read_bytes())==r['source_sha256']
 removed=sum(x['bytes'] for x in m['removed_verified_generated']);result=dict(md_sha256=digest,passed=True,numbered_roms_preserved=270,original_sms_preserved=True,release_identical_after_cleanup=True,recovered_bytes_verified=recovered,removed_generated_bytes=removed,net_bytes_freed=removed-sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
 (ROOT/'analysis/loot_render_recovery_v0270_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
