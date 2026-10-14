"""Preserve v0177 hero/foreground/audio baseline before further native edits."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/hero-init-v0177';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable research differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 names=['hero_initialization_cost.py','validate_hero_initialization_cost.py','build_hero_timing_core.py',
        'validate_live_hero_initialization_cost.py','paid_exit_foreground_cost.py','validate_paid_exit_foreground_cost.py',
        'profile_paid_exit_music_baseline.py','profile_paid_passage_loader_phases.py','reveal_loading_cost.py',
        'class0_graphics_loading_cost.py','world_map_loading_cost.py','map_hud_loading_cost.py',
        'full_actor_loading_cost.py','room_history_loading_cost.py','world_load_tail_cost.py',
        'source_rng_reference.py','hud_loading_cost.py','room_map_loading_cost.py','ram_plane_loading_cost.py',
        'actor_loading_cost.py','actor_reference.py','run_core.py','archive_hero_initialization_research.py']
 for name in names:preserve(ROOT/'tools'/name,'tools/'+name)
 for name in ['hero_initialization_cost_report.json','live_hero_initialization_cost_report.json','paid_exit_foreground_cost_report.json','paid_exit_music_baseline_report.json']:
  preserve(ROOT/'analysis'/name,'reports/'+name)
 for path in sorted((ROOT/'validation/paid-passage-hero-init').glob('*/*')):
  if path.is_file() and (path.name.endswith('-cycle-events.json') or '-hero-' in path.name):preserve(path,str(path.relative_to(ROOT)))
 for path in sorted((ROOT/'validation/paid-exit-music-baseline-v0177').glob('*.json')):preserve(path,str(path.relative_to(ROOT)))
 for path in sorted((ROOT/'validation/hero-initialization-cost').glob('*-results.bin')):preserve(path,str(path.relative_to(ROOT)))
 for name in ['hero-core-build.log','hero-initialization-cost.log','live-hero-initialization-cost.log','paid-exit-foreground-cost.log','paid-exit-music-baseline-v0177.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_hero_libretro.dll';preserve(core,core.name)
 for name in ['z80-before-hero.txt','z80-hero-snapshots.txt','README.md']:preserve(folder/name,name)
 assert (ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c').read_bytes()==(folder/'z80-before-hero.txt').read_bytes()
 prior=ROOT/'versions/v0177-3f4dbbc9';rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert rom==(prior/'gaw-megadrive-v0177.bin').read_bytes()
 for path in (ROOT/'megadrive/src').iterdir():
  if path.is_file():assert path.read_bytes()==(prior/'source'/path.name).read_bytes()
 data=(json.dumps(dict(production_version=177,production_sha256=hashlib.sha256(rom).hexdigest(),production_ROM_changed=False,files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('Preserved',len(items),'v0177 hero/foreground/audio-baseline files;production unchanged.')

if __name__=='__main__':main()
