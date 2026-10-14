"""Preserve v0176 timing/RNG research and raw profiles;assert production unchanged."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/transition-timing-v0176';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable archive differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for name in ['build_transition_timing_core.py','profile_paid_passage_loader_phases.py',
              'profile_paid_passage_transition_matrix.py','source_rng_reference.py',
              'validate_source_rng_seed_cost.py','room_history_loading_cost.py',
              'validate_live_room_history_loading_cost.py','world_load_tail_cost.py',
              'validate_live_world_load_tail_cost.py','archive_transition_timing_research.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for name in ['paid_passage_transition_matrix_report.json','source_rng_seed_cost_report.json',
              'live_room_history_loading_cost_report.json','live_world_load_tail_cost_report.json']:
  preserve(ROOT/'analysis'/name,'reports/'+name)
 for path in sorted((ROOT/'validation/paid-passage-transition-matrix').glob('*/*.json')):
  preserve(path,str(path.relative_to(ROOT)))
 for path in sorted((ROOT/'validation/source-rng-seed-cost').glob('*-seed-costs.bin')):
  preserve(path,str(path.relative_to(ROOT)))
 for name in ['transition-core-build.log','paid-passage-transition-matrix.log',
              'source-rng-seed-cost.log','live-room-history-loading-cost.log','live-world-load-tail-cost.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_transition_libretro.dll'
 preserve(core,core.name)
 for name in ['z80-before-transition-markers.txt','z80-transition-markers.txt','README.md']:
  preserve(folder/name,name)
 assert (ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c').read_bytes()==(folder/'z80-before-transition-markers.txt').read_bytes()
 prior=ROOT/'versions/v0176-9a4471c0';rom=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert rom==(prior/'gaw-megadrive-v0176.bin').read_bytes()
 for path in (ROOT/'megadrive/src').iterdir():
  if path.is_file():assert path.read_bytes()==(prior/'source'/path.name).read_bytes(),('production source changed',path.name)
 manifest=dict(production_version='v0176',production_sha256=hashlib.sha256(rom).hexdigest(),production_ROM_changed=False,files=items)
 data=(json.dumps(manifest,indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('Preserved',len(items),'timing/RNG research files; production v0176 unchanged.')

if __name__=='__main__':main()
