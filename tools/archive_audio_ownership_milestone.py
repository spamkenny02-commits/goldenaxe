"""Preserve v0182 F3 correction and bounded deterministic-command research."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-ownership-v0182';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():preserve(p,'source-v0182/'+p.name)
 preserve(ROOT/'versions/v0181-97313b55/source/sound.inc','source-v0181/sound.inc')
 for name in ['audio_note_sequence_cost.py','audio_dispatch_cost.py','validate_audio_note_commands_cost.py','validate_audio_note_ownership_cost.py','validate_audio_ownership.py','validate_audio_prefix_cost.py','audio_ownership_harness.c','build_audio_ownership_harness.ps1','audit_audio_ownership_patch.py','archive_audio_ownership_milestone.py']:preserve(ROOT/'tools'/name,'tools/'+name)
 for name in ['audio_note_commands_cost_report.json','audio_note_ownership_cost_report.json','audio_ownership_baseline_report.json','audio_ownership_report.json','audio_ownership_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for root in ['audio-note-commands','audio-note-sequence/ownership','audio-ownership','music-fade-dispatch']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json','.inc']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-note-commands-cost.log','audio-note-ownership-cost.log','audio-ownership-baseline.log','audio-ownership-fixed.log','build-audio-ownership-baseline.log','build-audio-ownership-fixed.log','build-v0182.log','music-v0182.log','sfx-v0182.log','music-fade-v0182.log','audio_ownership_patch_report.json','music_report.json','sfx_report.json','music_fade_dispatch_report.json']:preserve(ROOT/'validation'/name,'validation/'+name)
 for name in ['genesis_plus_gx_prefix_libretro.dll','genesis_plus_gx_tableenvelope_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 for p in sorted((ROOT.parents[1]/'work/audio-ownership-harness/src').iterdir()):
  if p.is_file():preserve(p,'native-harness/src/'+p.name)
 for name in ['rom.bin','symbol.txt']:preserve(ROOT.parents[1]/'work/audio-ownership-harness/out/release'/name,'native-harness/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert digest=='f41db51b8cb8356125c6b48f967a26bc775e63330cb87fb8f942b4e063fd848d'
 for name,count in [('audio_note_commands_cost_report.json',59904),('audio_note_ownership_cost_report.json',3840)]:
  r=json.loads((ROOT/'analysis'/name).read_text());assert r['cases']==count and r['md_sha256']=='97313b559898dcdc3a4d98623526f58c7b0b7565741882a02298de85a4358236'
 assert json.loads((ROOT/'analysis/audio_ownership_report.json').read_text())['all_cases_exact']
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('F3 correction and command evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
