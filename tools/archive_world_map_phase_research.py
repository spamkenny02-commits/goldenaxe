"""Archive original graphics andworld map load scheduling evidence without changing production."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/world-map-phase-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['build_world_map_phase_core','world_map_phase','validate_world_map_phase','profile_paid_passage_loader_phases','archive_world_map_phase_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/world-map-phase-v0183/z80-world-map-phase-extra.txt','z80-world-map-phase-extra.txt')
 for name in ['system.c','vdp_ctrl.c']:preserve(ROOT.parents[1]/'work/genesis-plus-gx/core'/name,'emulator-source/'+name)
 preserve(ROOT/'analysis/bank_00.asm','reference/bank_00.asm')
 suffixes=['-cycle-events.json','-audio-irq-events.json','-foreground-phase-records.bin','-map-extra-records.bin']
 for p in sorted((ROOT/'validation/world-map-phase').rglob('*')):
  if p.is_file() and (any(p.name.endswith(s) for s in suffixes) or p.name=='capture.json'):preserve(p,str(p.relative_to(ROOT)))
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text());preserve(ROOT/'analysis/paid_passage_reference.json','reference/paid_passage_reference.json')
 for town,*_ in routes['routes']:
  for mask in [0,255]:
   for region in ['auto','pal']:
    p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['build-world-map-phase.log','world-map-phase-core-build.log','world-map-phase-live.log','world-map-phase-group1.log','world-map-phase-group2.log','world-map-phase-group3.log','world-map-phase-prediction.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 report=json.loads((ROOT/'analysis/world_map_phase_report.json').read_text());assert report['cases']==24 and report['md_sha256']==digest
 for name in ['world_map_phase_report.json','world_map_phase_milestone.md']:preserve(ROOT/'analysis'/name,name)
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_worldmapphaseextra_libretro.dll','genesis_plus_gx_worldmapphaseextra_libretro.dll')
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Graphics andworld map load scheduling evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
