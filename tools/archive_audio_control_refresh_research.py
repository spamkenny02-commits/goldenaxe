"""Archive original dispatch/priority-effect M1/R/state/timing checks."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-control-refresh-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['audio_dispatch_refresh','audio_priority_effect_refresh','validate_audio_dispatch_refresh','validate_audio_priority_effect_refresh','build_audio_prefix_refresh_core','archive_audio_control_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/audio-prefix-refresh-v0183/z80-audio-prefix-refresh.txt','z80-audio-prefix-refresh.txt');preserve(ROOT/'analysis/bank_06.asm','reference/bank_06.asm')
 for dirname,kind in [('audio-dispatch-refresh','dispatch'),('audio-priority-effect-refresh','priority')]:
  base=ROOT/'validation'/dirname/kind;preserve(base/'source.sms',str((base/'source.sms').relative_to(ROOT)))
  for region in ['auto','pal']:
   for p in [base/f'{region}-results.bin',base/region/'capture.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-dispatch-refresh.log','audio-priority-effect-refresh.log','audio-prefix-refresh-core-build.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('audio_dispatch_refresh_report.json',48000),('audio_priority_effect_refresh_report.json',33480)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest;preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/audio_control_refresh_milestone.md','audio_control_refresh_milestone.md')
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_prefixrefresh_libretro.dll','genesis_plus_gx_prefixrefresh_libretro.dll')
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Audio control M1/R evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
