"""Preserve original music/effect/control dispatcher model and evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-dispatch-v0180';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0180-3f155979/source'/p.name).read_bytes(),('production changed',p.name)
 preserve(folder/'z80-live-prefix.txt','z80-live-prefix.txt')
 for name in ['audio_dispatch_cost.py','validate_audio_dispatch_cost.py','validate_live_audio_dispatch_cost.py','build_audio_prefix_live_core.py','validate_audio_prefix_cost.py','audio_prefix_cost.py','audio_arbitration_cost.py','profile_paid_passage_loader_phases.py','archive_audio_dispatch_research.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for root in ['audio-dispatch','audio-dispatch-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-dispatch-cost.log','audio-dispatch-live.log','audio-dispatch-live-core-build.log','build-audio-dispatch-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['audio_dispatch_cost_report.json','live_audio_dispatch_cost_report.json','audio_dispatch_milestone.md']:preserve(ROOT/'analysis'/name,name)
 preserve(ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_dispatch_libretro.dll','genesis_plus_gx_dispatch_libretro.dll')
 unit=json.loads((ROOT/'analysis/audio_dispatch_cost_report.json').read_text());live=json.loads((ROOT/'analysis/live_audio_dispatch_cost_report.json').read_text())
 assert unit['cases']==48000 and live['cases']==4808 and live['dispatch_cases']==1202
 assert unit['md_sha256']==live['md_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 data=(json.dumps(dict(md_sha256=unit['md_sha256'],source_sha256=unit['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original dispatcher evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
