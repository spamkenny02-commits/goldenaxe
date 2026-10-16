"""Freeze gated IRQ M1/R tools, observer and conditional validation evidence."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/full-irq-refresh-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes()
 pending=['full_irq_refresh','validate_full_irq_refresh','build_full_irq_refresh_core','validate_live_full_irq_refresh','profile_paid_passage_loader_phases','archive_full_irq_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/full-irq-refresh-v0183/z80-full-irq-refresh.txt','z80-full-irq-refresh.txt')
 preserve(ROOT/'validation/full-irq-unit/full-irq/source.sms','fixture/source.sms')
 for name in ['bank_00.asm','bank_06.asm','full_irq_unit_report.json','paid_passage_reference.json']:
  preserve(ROOT/'analysis'/name,'reference/'+name)
 for region in ['auto','pal']:
  for suffix in ['records.bin','m1.bin']:preserve(ROOT/f'validation/full-irq-refresh-unit/{region}-{suffix}',f'unit/{region}-{suffix}')
 for town,*_ in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']:
  for mask in [0,255]:
   for region in ['auto','pal']:
    root=ROOT/f'validation/full-irq-refresh-live/{town:02x}-{mask:02x}'
    for suffix in ['cycle-events.json','audio-irq-events.json','full-irq-records.bin','full-irq-m1-records.bin','live-envelope-records.bin']:
     p=root/f'{region}-{suffix}';preserve(p,str(p.relative_to(ROOT)))
    for suffix in ['full-irq-records.bin','live-envelope-records.bin']:
     p=ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-{suffix}';preserve(p,'reference/'+str(p.relative_to(ROOT)))
    p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('full_irq_refresh_unit_report.json',2880),('live_full_irq_refresh_report.json',24)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest
  if count==24:assert report['IRQ_calls']==13749
  preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/full_irq_refresh_milestone.md','full_irq_refresh_milestone.md')
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_fullirqrefresh_libretro.dll','genesis_plus_gx_fullirqrefresh_libretro.dll')
 for name in ['build-full-irq-refresh.log','full-irq-refresh-core-build.log','full-irq-refresh-unit.log','full-irq-refresh-live-6d-ff.log','full-irq-refresh-live-group0.log','full-irq-refresh-live-group1.log','full-irq-refresh-live-group2.log','live-full-irq-refresh.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Gated IRQ M1/R evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
