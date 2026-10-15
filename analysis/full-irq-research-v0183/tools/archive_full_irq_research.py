"""Archive gatedIRQ models and required evidence for conditional loading budgets."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/full-irq-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['full_irq_cost','build_full_irq_core','validate_full_irq_cost','validate_full_irq_unit','validate_complete_loading_budget','profile_paid_passage_loader_phases','archive_full_irq_research'];seen=set()
 while pending:
  name=pending.pop();p=ROOT/'tools'/f'{name}.py'
  if name in seen or not p.exists():continue
  seen.add(name);preserve(p,'tools/'+p.name)
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/full-irq-v0183/z80-full-irq.txt','z80-full-irq.txt')
 suffixes=['-cycle-events.json','-audio-irq-events.json','-live-envelope-records.bin','-full-irq-records.bin','-save-wait-records.bin']
 for p in sorted((ROOT/'validation/full-irq').rglob('*')):
  if p.is_file() and (any(p.name.endswith(s) for s in suffixes) or p.name=='capture.json' or '-hero-' in p.name and p.name.endswith('-before.bin')):preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation/full-irq-unit').rglob('*')):
  if p.is_file() and (p.name in ['source.sms','capture.json'] or p.name.endswith('-records.bin')):preserve(p,str(p.relative_to(ROOT)))
 hero=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text());preserve(ROOT/'analysis/live_hero_initialization_cost_report.json','reference/live_hero_initialization_cost_report.json')
 for row in hero['rows']:
  preserve(ROOT/row['snapshot_path'],'reference/'+row['snapshot_path'])
  p=ROOT/f"versions/v0179-d018ed93/validation/paid-exit-music/{row['town']:02x}-{row['mask']:02x}/{row['region']}-cycle-events.json";preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-full-irq-core.log','full-irq-core-build.log','full-irq-live.log','full-irq-group1.log','full-irq-group2.log','full-irq-group3.log','full-irq-cost.log','full-irq-unit.log','complete-loading-budget.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['full_irq_cost_report.json','full_irq_unit_report.json','complete_loading_budget_report.json','full_irq_milestone.md']:preserve(ROOT/'analysis'/name,name)
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_fullirq_libretro.dll','genesis_plus_gx_fullirq_libretro.dll')
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 live=json.loads((ROOT/'analysis/full_irq_cost_report.json').read_text());unit=json.loads((ROOT/'analysis/full_irq_unit_report.json').read_text());budget=json.loads((ROOT/'analysis/complete_loading_budget_report.json').read_text())
 assert live['cases']==13749 and live['paths']==24 and live['reader_cases']==14424 and all(not r['unsupported_cases'] for r in live['rows'])
 assert unit['cases']==2880 and budget['cases']==24 and sum(r['loading_full_IRQs'] for r in budget['rows'])==48
 assert all(r['md_sha256']==digest for r in [live,unit,budget])
 data=(json.dumps(dict(md_sha256=digest,source_sha256=live['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('FullIRQ/conditional loading evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
