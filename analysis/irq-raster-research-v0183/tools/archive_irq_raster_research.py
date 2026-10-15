"""Archive raster-to-palette predictions and local VCounter oracle comparison."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/irq-raster-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['irq_raster_phase','build_irq_raster_core','build_vcounter_oracle','validate_vcounter_phase_unit','validate_irq_raster_phase','validate_raster_loading_budget','profile_paid_passage_loader_phases','archive_irq_raster_research'];seen=set()
 while pending:
  name=pending.pop();p=ROOT/'tools'/f'{name}.py'
  if name in seen or not p.exists():continue
  seen.add(name);preserve(p,'tools/'+p.name)
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/irq-raster-v0183/z80-irq-raster.txt','z80-irq-raster.txt');preserve(ROOT/'analysis/vcounter-oracle-v0183/z80-vcounter-oracle.txt','z80-vcounter-oracle.txt')
 for name in ['vdp_ctrl.c','memz80.c','system.h']:preserve(ROOT.parents[1]/'work/genesis-plus-gx/core'/name,'emulator-source/'+name)
 suffixes=['-cycle-events.json','-audio-irq-events.json','-live-envelope-records.bin','-full-irq-records.bin','-save-wait-records.bin','-irq-raster-records.bin']
 for p in sorted((ROOT/'validation/irq-raster').rglob('*')):
  if p.is_file() and (any(p.name.endswith(s) for s in suffixes) or p.name=='capture.json' or '-hero-' in p.name and p.name.endswith('-before.bin')):preserve(p,str(p.relative_to(ROOT)))
 hero=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text());preserve(ROOT/'analysis/live_hero_initialization_cost_report.json','reference/live_hero_initialization_cost_report.json')
 for row in hero['rows']:
  preserve(ROOT/row['snapshot_path'],'reference/'+row['snapshot_path'])
  p=ROOT/f"versions/v0179-d018ed93/validation/paid-exit-music/{row['town']:02x}-{row['mask']:02x}/{row['region']}-cycle-events.json";preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-irq-raster-core.log','irq-raster-core-build.log','irq-raster-live.log','irq-raster-group1.log','irq-raster-group2.log','irq-raster-group3.log','irq-raster-phase.log','build-vcounter-oracle-core.log','vcounter-oracle-core-build.log','vcounter-phase-unit.log','raster-loading-budget.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['irq_raster_phase_report.json','vcounter_phase_unit_report.json','raster_loading_budget_report.json','irq_raster_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_irqraster_libretro.dll','genesis_plus_gx_vcounteroracle_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 reports=[json.loads((ROOT/'analysis'/n).read_text()) for n in ['irq_raster_phase_report.json','vcounter_phase_unit_report.json','raster_loading_budget_report.json']]
 assert reports[0]['cases']==13749 and reports[0]['paths']==24 and reports[1]['cases']==149500 and reports[2]['cases']==24
 assert all(r['md_sha256']==digest for r in reports)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=reports[0]['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Raster/palette prediction evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
