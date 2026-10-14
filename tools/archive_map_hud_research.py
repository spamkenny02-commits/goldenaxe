"""Preserve map/HUD models and evidence without releasing an unchanged ROM."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/loading-map-hud-v0175';folder.mkdir(exist_ok=True)
 files=[
  'tools/hud_loading_cost.py','tools/validate_hud_loading_cost.py',
  'tools/world_map_loading_cost.py','tools/validate_world_map_loading_cost.py',
  'tools/map_hud_loading_cost.py','tools/validate_live_map_hud_loading_cost.py',
  'tools/validate_paid_passage_loading_phase_costs.py','tools/archive_map_hud_research.py',
  'analysis/hud_loading_cost_report.json','analysis/world_map_loading_cost_report.json',
  'analysis/live_map_hud_loading_cost_report.json','analysis/paid_passage_loading_phase_costs_report.json',
  'validation/hud-loading-cost.log','validation/world-map-loading-cost.log',
  'validation/live-map-hud-loading-cost.log','validation/paid-passage-loading-phase-costs.log']
 manifest=[]
 for relative in files:
  data=(ROOT/relative).read_bytes();target=folder/relative;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable archive differs',relative)
  else:
   with target.open('xb') as handle:handle.write(data)
  manifest.append(dict(path=relative,sha256=hashlib.sha256(data).hexdigest()))
 production=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert production==(ROOT/'versions/v0175-82520cf7/gaw-megadrive-v0175.bin').read_bytes()
 prior=ROOT/'analysis/loading-graphics-v0175/manifest.json'
 result=dict(production_version='v0175',production_sha256=hashlib.sha256(production).hexdigest(),production_ROM_changed=False,prior_graphics_core_and_evidence_manifest_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),files=manifest)
 data=(json.dumps(result,indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('Preserved',len(manifest),'map/HUD research files; production v0175 unchanged.')

if __name__=='__main__':main()
