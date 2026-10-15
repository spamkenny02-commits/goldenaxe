"""Preserve wait-loop observations and complete controlled loading accounting."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/save-wait-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['build_save_wait_core','save_wait_cost','validate_save_wait_foreground','profile_paid_passage_loader_phases','archive_save_wait_research'];seen=set()
 while pending:
  name=pending.pop();p=ROOT/'tools'/f'{name}.py'
  if name in seen or not p.exists():continue
  seen.add(name);preserve(p,'tools/'+p.name)
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/save-wait-v0183/z80-save-wait.txt','z80-save-wait.txt')
 for p in sorted((ROOT/'validation/save-wait').rglob('*')):
  if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 hero=json.loads((ROOT/'analysis/live_hero_initialization_cost_report.json').read_text())
 preserve(ROOT/'analysis/live_hero_initialization_cost_report.json','reference/live_hero_initialization_cost_report.json')
 for row in hero['rows']:
  preserve(ROOT/row['snapshot_path'],'reference/'+row['snapshot_path'])
  p=ROOT/f"versions/v0179-d018ed93/validation/paid-exit-music/{row['town']:02x}-{row['mask']:02x}/{row['region']}-cycle-events.json";preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-save-wait-core.log','save-wait-core-build.log','save-wait-live.log','save-wait-group1.log','save-wait-group2.log','save-wait-group3.log','save-wait-foreground.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['save_wait_foreground_report.json','save_wait_milestone.md']:preserve(ROOT/'analysis'/name,name)
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_savewait_libretro.dll','genesis_plus_gx_savewait_libretro.dll')
 report=json.loads((ROOT/'analysis/save_wait_foreground_report.json').read_text());digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert report['cases']==24 and report['wait_records']==13725 and report['reader_records']==14424
 assert digest==report['md_sha256']=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 assert all(row['unexplained_foreground_master_cycles']==0 for row in report['rows'])
 data=(json.dumps(dict(md_sha256=digest,source_sha256=report['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Wait/loading accounting evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
