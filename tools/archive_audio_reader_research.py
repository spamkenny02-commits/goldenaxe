"""Archive original8000 reader composition,priority/gate fixtures and DE proofs."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-reader-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 names=['audio_reader_cost.py','audio_priority_effect_cost.py','audio_arbitration_cost.py','audio_prefix_cost.py','audio_dispatch_cost.py','audio_tone_channel_cost.py','audio_noise_channel_cost.py','audio_noise_note_cost.py','audio_note_sequence_cost.py','audio_pitch_cost.py','audio_adsr_cost.py','audio_table_envelope_cost.py','validate_audio_priority_effect_cost.py','validate_audio_reader_gates_cost.py','validate_live_audio_reader_cost.py','validate_audio_tone_channel_cost.py','validate_audio_noise_channel_cost.py','validate_live_tone_channel_cost.py','validate_live_noise_channel_cost.py','validate_audio_prefix_cost.py','build_live_envelope_core.py','profile_paid_passage_loader_phases.py','archive_audio_reader_research.py']
 for name in names:preserve(ROOT/'tools'/name,'tools/'+name)
 preserve(ROOT/'analysis/audio-reader-complete-live-v0183/z80-live-reader.txt','z80-live-reader.txt')
 preserve(ROOT/'analysis/audio-table-envelope-v0180/z80-envelope-unit.txt','z80-envelope-unit.txt')
 for root in ['audio-priority-effect','audio-reader-gates','audio-reader-complete-live','audio-tone-channel','audio-noise-channel']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for region in ['auto','pal']:preserve(ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json',f'reference-v0179/{region}-cycle-events.json')
 for name in ['audio-priority-effect-cost.log','audio-reader-gates-cost.log','tone-channel-de-cost.log','noise-channel-de-cost.log','live-tone-de-cost.log','live-noise-de-cost.log','audio-reader-complete-live.log','live-audio-reader-cost.log','build-audio-reader-complete-live-core.log','audio-reader-complete-live-core-build.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 reports={'audio_priority_effect_cost_report.json':33480,'audio_reader_gates_cost_report.json':10752,'audio_tone_channel_cost_report.json':20680,'audio_noise_channel_cost_report.json':39360,'live_audio_reader_cost_report.json':1202,'live_tone_channel_cost_report.json':3372,'live_noise_channel_cost_report.json':1102}
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in reports.items():
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest;preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/audio_reader_milestone.md','audio_reader_milestone.md')
 for name in ['genesis_plus_gx_tableenvelope_libretro.dll','genesis_plus_gx_livereadercomplete_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 live=json.loads((ROOT/'analysis/live_audio_reader_cost_report.json').read_text());assert all(not r['unsupported_command_cases'] and r['captured_cases']==r['IRQ_reader_calls']==601 for r in live['rows'])
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Reader composition evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
