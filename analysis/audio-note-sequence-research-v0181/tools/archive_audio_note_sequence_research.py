"""Archive bounded8357 note/control cost research against unchanged v0181."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-note-sequence-research-v0181';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'versions/v0181-97313b55/source'/p.name).read_bytes(),('production changed',p.name)
 for name in ['audio_note_sequence_cost.py','audio_dispatch_cost.py','build_live_envelope_core.py','validate_audio_note_sequence_cost.py','validate_audio_note_termination_cost.py','validate_live_note_sequence_cost.py','validate_audio_prefix_cost.py','profile_paid_passage_loader_phases.py','archive_audio_note_sequence_research.py']:preserve(ROOT/'tools'/name,'tools/'+name)
 preserve(ROOT/'analysis/audio-note-sequence-live-v0180/z80-live-notes.txt','z80-live-notes.txt')
 for root in ['audio-note-sequence','audio-note-sequence-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for name in ['audio-note-sequence-cost.log','audio-note-termination-cost.log','audio-note-sequence-live-cost.log','audio-notes-live.log','audio-note-sequence-live-core-build.log','build-audio-notes-live-core.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 reports=['audio_note_sequence_cost_report.json','audio_note_termination_cost_report.json','live_note_sequence_cost_report.json']
 for name in reports+['audio_note_sequence_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_prefix_libretro.dll','genesis_plus_gx_tableenvelope_libretro.dll','genesis_plus_gx_livenotes_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert digest=='97313b559898dcdc3a4d98623526f58c7b0b7565741882a02298de85a4358236'
 for name,count in zip(reports,[103424,384,212]):
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest
 data=(json.dumps(dict(md_sha256=digest,files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Original note/control evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
