"""Freeze native clock source, reference scheduler and host/68000 evidence."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/native-source-clock-v0183-r1';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 additions=['source_rng.c','source_rng.h','source_clock.c','source_clock.h']
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name not in additions:assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes()
 for name in ['source_rng.c','source_rng.h']:assert (ROOT/'megadrive/src'/name).read_bytes()==(ROOT/'analysis/native-source-rng-v0183/megadrive/src'/name).read_bytes()
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name in additions:preserve(ROOT/'megadrive/src'/name,'megadrive/src/'+name)
 pending=['validate_native_source_clock','validate_native_source_clock_68k','archive_native_source_clock'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 for name in ['native_source_clock_report.json','native_source_clock_68k_report.json','native_source_clock_milestone.md']:preserve(ROOT/'analysis'/name,'analysis/'+name)
 for name in ['native-source-clock.log','native-source-clock-68k.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for p in sorted((ROOT/'validation/native-source-clock').iterdir()):
  if p.is_file():preserve(p,str(p.relative_to(ROOT)))
 base=ROOT/'validation/native-clock-68k'
 for p in sorted((base/'src').iterdir()):preserve(p,str(p.relative_to(ROOT)))
 for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:preserve(base/name,'validation/native-clock-68k/'+name)
 host=json.loads((ROOT/'analysis/native_source_clock_report.json').read_text());cpu=json.loads((ROOT/'analysis/native_source_clock_68k_report.json').read_text())
 assert host['cases']==7669 and host['rejected_cases']==5 and host['suppression_cases']==480 and host['coalescence_cases']==340
 assert len(cpu['rows'])==2 and all((r['done'],r['cases'],r['failures'],r['rejections'])==(1,7669,0,5) for r in cpu['rows'])
 data=(json.dumps(dict(production_md_sha256=digest,source_sms_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Native clock source and execution evidence archived:',len(items),'files')
if __name__=='__main__':main()
