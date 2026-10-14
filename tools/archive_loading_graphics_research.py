"""Preserve verified source loader research without releasing an unchanged ROM."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/loading-graphics-v0175';folder.mkdir(exist_ok=True)
 files=[
  'tools/ram_plane_loading_cost.py','tools/validate_ram_plane_loading_cost.py',
  'tools/class0_graphics_loading_cost.py','tools/validate_class0_graphics_loading_cost.py',
  'tools/room_map_loading_cost.py','tools/validate_paid_passage_loading_phase_costs.py',
  'tools/profile_paid_passage_loader_phases.py','tools/build_timing_core.py',
  'tools/archive_loading_graphics_research.py',
  'analysis/ram_plane_loading_cost_report.json','analysis/class0_graphics_loading_cost_report.json',
  'analysis/paid_passage_loading_phase_costs_report.json',
  'analysis/loading-model-v0175/z80-loader-markers.txt',
  'validation/paid_passage_loader_phases_report.json',
  'validation/paid-passage-loader/auto-cycle-events.json',
  'validation/paid-passage-loader/pal-cycle-events.json',
  'validation/ram-plane-loading-cost.log','validation/class0-graphics-loading-cost.log',
  'validation/paid-passage-loading-phase-costs.log','validation/loader-core-build.log']
 manifest=[]
 for relative in files:
  data=(ROOT/relative).read_bytes();target=folder/relative;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable archive differs',relative)
  else:
   with target.open('xb') as handle:handle.write(data)
  manifest.append(dict(path=relative,sha256=hashlib.sha256(data).hexdigest()))
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loader_libretro.dll'
 data=core.read_bytes();target=folder/core.name
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 manifest.append(dict(path=core.name,sha256=hashlib.sha256(data).hexdigest()))
 production=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert production==(ROOT/'versions/v0175-82520cf7/gaw-megadrive-v0175.bin').read_bytes()
 result=dict(production_version='v0175',production_sha256=hashlib.sha256(production).hexdigest(),production_ROM_changed=False,files=manifest)
 data=(json.dumps(result,indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('Preserved',len(manifest),'research files; production v0175 unchanged.')

if __name__=='__main__':main()
