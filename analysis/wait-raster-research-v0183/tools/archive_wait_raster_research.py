"""Archive wait scheduling predictions,entry states and controlled latch/EI fixtures."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/wait-raster-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['build_wait_raster_core','wait_raster_prediction','validate_wait_raster_prediction','validate_wait_raster_unit','validate_wait_predicted_loading_budget','profile_paid_passage_loader_phases','archive_wait_raster_research'];seen=set()
 while pending:
  name=pending.pop();p=ROOT/'tools'/f'{name}.py'
  if name in seen or not p.exists():continue
  seen.add(name);preserve(p,'tools/'+p.name)
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/wait-raster-v0183/z80-wait-raster.txt','z80-wait-raster.txt')
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/core/system.c','emulator-source/system.c')
 suffixes=['-cycle-events.json','-audio-irq-events.json','-live-envelope-records.bin','-full-irq-records.bin','-save-wait-records.bin','-irq-raster-records.bin','-wait-entry-records.bin']
 for p in sorted((ROOT/'validation/wait-raster').rglob('*')):
  if p.is_file() and (any(p.name.endswith(s) for s in suffixes) or p.name=='capture.json' or '-hero-' in p.name and p.name.endswith('-before.bin')):preserve(p,str(p.relative_to(ROOT)))
 for name in ['wait-raster-unit','wait-raster-unit-pal']:
  base=ROOT/'validation'/name/'wait';preserve(base/'source.sms',f'validation/{name}/wait/source.sms')
  for region in ['auto','pal']:
   for filename in [f'{region}-waits.bin',f'{region}-entries.bin',f'{region}-irq-offsets.json',f'{region}/capture.json']:
    p=base/filename
    if p.exists():preserve(p,str(p.relative_to(ROOT)))
 hero=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text());preserve(ROOT/'analysis/live_hero_initialization_cost_report.json','reference/live_hero_initialization_cost_report.json')
 for row in hero['rows']:
  preserve(ROOT/row['snapshot_path'],'reference/'+row['snapshot_path'])
  p=ROOT/f"versions/v0179-d018ed93/validation/paid-exit-music/{row['town']:02x}-{row['mask']:02x}/{row['region']}-cycle-events.json";preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-wait-raster-core.log','wait-raster-core-build.log','wait-raster-live.log','wait-raster-group1.log','wait-raster-group2.log','wait-raster-group3.log','wait-raster-prediction.log','wait-raster-unit.log','wait-raster-pal-latched-unit.log','wait-predicted-loading-budget.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 reports=['wait_raster_prediction_report.json','wait_raster_unit_report.json','wait_raster_pal_latched_unit_report.json','wait_predicted_loading_budget_report.json']
 for name in reports+['wait_raster_milestone.md']:preserve(ROOT/'analysis'/name,name)
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitraster_libretro.dll','genesis_plus_gx_waitraster_libretro.dll')
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in zip(reports,[13725,4608,1548,24]):
  r=json.loads((ROOT/'analysis'/name).read_text());assert r['cases']==count and r['md_sha256']==digest
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Wait scheduling evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
