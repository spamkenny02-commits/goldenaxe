"""Preserve original pitch/vibrato models,fixtures and read-only observations."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-pitch-research-v0180';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0180-3f155979/source'/p.name).read_bytes(),('production changed',p.name)
 preserve(ROOT/'analysis/audio-pitch-v0180/z80-pitch-unit.txt','z80-pitch-unit.txt')
 preserve(ROOT/'analysis/audio-pitch-live-v0180/z80-live-pitch.txt','z80-live-pitch.txt')
 for name in ['audio_pitch_cost.py','audio_dispatch_cost.py','build_audio_pitch_core.py','build_live_envelope_core.py','validate_audio_pitch_cost.py','validate_live_pitch_cost.py','validate_audio_prefix_cost.py','profile_paid_passage_loader_phases.py','archive_audio_pitch_research.py']:preserve(ROOT/'tools'/name,'tools/'+name)
 for root in ['audio-pitch','audio-pitch-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-pitch-cost.log','audio-pitch-live.log','audio-pitch-core-build.log','audio-pitch-live-core-build.log','build-audio-pitch-core.log','build-audio-pitch-live-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['audio_pitch_cost_report.json','live_pitch_cost_report.json','audio_pitch_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_pitch_libretro.dll','genesis_plus_gx_livepitch_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 unit=json.loads((ROOT/'analysis/audio_pitch_cost_report.json').read_text());live=json.loads((ROOT/'analysis/live_pitch_cost_report.json').read_text())
 assert unit['cases']==118800 and live['cases']==181
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert unit['md_sha256']==live['md_sha256']==digest
 data=(json.dumps(dict(md_sha256=digest,source_sha256=unit['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original pitch evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
