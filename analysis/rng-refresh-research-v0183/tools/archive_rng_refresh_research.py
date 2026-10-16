"""Archive isolated RNG output and live observed-entry-R checks."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/rng-refresh-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['build_rng_refresh_core','source_rng_refresh','validate_rng_refresh','validate_live_rng_refresh','profile_paid_passage_loader_phases','archive_rng_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/rng-refresh-v0183/z80-rng-refresh.txt','z80-rng-refresh.txt');preserve(ROOT/'analysis/bank_00.asm','reference/bank_00.asm')
 for dirname in ['rng-refresh-seeds','rng-refresh-matrix/rng']:
  base=ROOT/'validation'/dirname;preserve(base/'source.sms',str((base/'source.sms').relative_to(ROOT)))
  for region in ['auto','pal']:
   for p in [base/f'{region}-rng-records.bin',base/region/'capture.json']:preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation/rng-refresh-live').rglob('*')):
  if p.is_file() and (p.name.endswith(('-cycle-events.json','-rng-refresh-records.bin')) or p.name=='capture.json'):preserve(p,str(p.relative_to(ROOT)))
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text());preserve(ROOT/'analysis/paid_passage_reference.json','reference/paid_passage_reference.json')
 for town,*_ in routes['routes']:
  for mask in [0,255]:
   for region in ['auto','pal']:
    p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-rng-refresh.log','rng-refresh-core-build.log','rng-refresh.log','rng-refresh-live.log','rng-refresh-live-group1.log','rng-refresh-live-group2.log','rng-refresh-live-group3.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('rng_refresh_report.json',135168),('live_rng_refresh_report.json',24)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest;preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/rng_refresh_milestone.md','rng_refresh_milestone.md')
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_rngrefresh_libretro.dll','genesis_plus_gx_rngrefresh_libretro.dll')
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('RNG refresh/output evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
