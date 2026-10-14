"""Retain independent helper models,isolated/live records and read-only cores."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-prefix-v0180';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0180-3f155979/source'/p.name).read_bytes(),('production changed',p.name)
 for name in ['z80-prefix-snapshots.txt','z80-live-prefix.txt']:preserve(folder/name,name)
 for name in ['audio_prefix_cost.py','build_audio_prefix_core.py','build_audio_prefix_live_core.py','validate_audio_prefix_cost.py','validate_live_audio_prefix_cost.py','profile_paid_passage_loader_phases.py','archive_audio_prefix_research.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for root in ['audio-prefix','audio-prefix-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.bin','.sms','.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-prefix-cost.log','audio-prefix-live.log','audio-prefix-core-build.log','audio-prefix-live-core-build.log','build-audio-prefix-core.log','build-audio-prefix-live-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['audio_prefix_cost_report.json','live_audio_prefix_cost_report.json','audio_prefix_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_prefix_libretro.dll','genesis_plus_gx_liveprefix_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 unit=json.loads((ROOT/'analysis/audio_prefix_cost_report.json').read_text());live=json.loads((ROOT/'analysis/live_audio_prefix_cost_report.json').read_text())
 assert unit['cases']==10240 and live['cases']==2404
 assert unit['md_sha256']==live['md_sha256']==hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 data=(json.dumps(dict(md_sha256=unit['md_sha256'],source_sha256=unit['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original tempo/fade evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
