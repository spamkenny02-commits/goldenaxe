"""Archive original864F composed M1/R/state/cost/DE unit andlive checks."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-noise-refresh-research-v0183-r1';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['generate_noise_channel_refresh','audio_noise_channel_refresh','audio_noise_channel_cost','audio_note_sequence_cost','validate_audio_noise_channel_refresh','validate_live_noise_refresh','build_live_noise_refresh_core','profile_paid_passage_loader_phases','validate_audio_noise_channel_cost','archive_audio_noise_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/audio-noise-refresh-live-v0183/z80-live-noise-refresh.txt','z80-live-noise-refresh.txt');preserve(ROOT/'analysis/audio-envelope-refresh-v0183/z80-envelope-refresh.txt','z80-envelope-refresh.txt');preserve(ROOT/'analysis/bank_06.asm','reference/bank_06.asm')
 base=ROOT/'validation/audio-noise-channel-refresh/noise';preserve(base/'source.sms',str((base/'source.sms').relative_to(ROOT)))
 for region in ['auto','pal']:
  for p in [base/f'{region}-results.bin',base/region/'capture.json']:preserve(p,str(p.relative_to(ROOT)))
  for suffix in ['cycle-events.json','live-envelope-records.bin','live-envelope-m1-records.bin']:
   p=ROOT/f'validation/noise-refresh-live/6d-ff/{region}-{suffix}';preserve(p,str(p.relative_to(ROOT)))
  for tag in ['sms','md']:
   p=ROOT/f'validation/noise-refresh-live/6d-ff/captures-{region}-{tag}/capture.json';preserve(p,str(p.relative_to(ROOT)))
  p=ROOT/f'validation/audio-noise-channel-live/6d-ff/{region}-live-envelope-records.bin';preserve(p,'reference/'+str(p.relative_to(ROOT)))
  p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['audio_noise_channel_cost_report.json','live_noise_channel_cost_report.json']:preserve(ROOT/'analysis'/name,'reference/'+name)
 for name in ['audio-noise-channel-refresh.log','build-live-noise-refresh.log','audio-live-noise-refresh-core-build.log','live-noise-refresh.log','live-noise-refresh-validation.log','generate-noise-channel-refresh.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('audio_noise_channel_refresh_report.json',39360),('live_noise_refresh_report.json',1102)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest;preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/audio_noise_channel_refresh_milestone.md','audio_noise_channel_refresh_milestone.md')
 for name in ['genesis_plus_gx_enveloperefresh_libretro.dll','genesis_plus_gx_livenoiserefresh_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Noise channel M1/R evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
