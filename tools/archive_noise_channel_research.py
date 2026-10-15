"""Archive bounded864F noise-channel composition and read-only live observations."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-noise-channel-research-v0183';items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 for name in ['audio_noise_channel_cost.py','audio_noise_note_cost.py','audio_adsr_cost.py','audio_table_envelope_cost.py','audio_dispatch_cost.py','validate_audio_noise_channel_cost.py','validate_live_noise_channel_cost.py','validate_audio_prefix_cost.py','build_live_envelope_core.py','profile_paid_passage_loader_phases.py','archive_noise_channel_research.py']:preserve(ROOT/'tools'/name,'tools/'+name)
 preserve(ROOT/'analysis/audio-noise-channel-live-v0183/z80-live-noise-channel.txt','z80-live-noise-channel.txt')
 preserve(ROOT/'analysis/audio-table-envelope-v0180/z80-envelope-unit.txt','z80-envelope-unit.txt')
 for root in ['audio-noise-channel','audio-noise-channel-live']:
  for p in sorted((ROOT/'validation'/root).rglob('*')):
   if p.is_file() and p.suffix in ['.sms','.bin','.json']:preserve(p,str(p.relative_to(ROOT)))
 for region in ['auto','pal']:preserve(ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json',f'reference-v0179/{region}-cycle-events.json')
 for name in ['audio-noise-channel-cost.log','audio-noise-channel-live.log','live-noise-channel-cost.log','build-audio-noise-channel-live-core.log','audio-noise-channel-live-core-build.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 for name in ['audio_noise_channel_cost_report.json','live_noise_channel_cost_report.json','audio_noise_channel_milestone.md']:preserve(ROOT/'analysis'/name,name)
 for name in ['genesis_plus_gx_tableenvelope_libretro.dll','genesis_plus_gx_livenoisechannel_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 unit=json.loads((ROOT/'analysis/audio_noise_channel_cost_report.json').read_text());live=json.loads((ROOT/'analysis/live_noise_channel_cost_report.json').read_text())
 assert unit['cases']==39360 and live['cases']==1102 and all(not r['unsupported_command_cases'] for r in live['rows'])
 assert sum(sum(r['initial_control_commands'].values()) for r in live['rows'])==32
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 assert digest==unit['md_sha256']==live['md_sha256']=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 data=(json.dumps(dict(md_sha256=digest,source_sha256=unit['source_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Noise-channel cost evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
