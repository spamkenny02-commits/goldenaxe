"""Archive original84C7 composed M1/R/state/cost/DE unit andlive checks."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-tone-refresh-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['generate_tone_channel_refresh','audio_tone_channel_refresh','audio_tone_channel_cost','audio_note_sequence_cost','validate_audio_tone_channel_refresh','validate_live_tone_refresh','build_live_tone_refresh_core','profile_paid_passage_loader_phases','validate_audio_tone_channel_cost','archive_audio_tone_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/audio-tone-refresh-live-v0183/z80-live-tone-refresh.txt','z80-live-tone-refresh.txt');preserve(ROOT/'analysis/audio-envelope-refresh-v0183/z80-envelope-refresh.txt','z80-envelope-refresh.txt');preserve(ROOT/'analysis/bank_06.asm','reference/bank_06.asm')
 base=ROOT/'validation/audio-tone-channel-refresh/tone';preserve(base/'source.sms',str((base/'source.sms').relative_to(ROOT)))
 for region in ['auto','pal']:
  for p in [base/f'{region}-results.bin',base/region/'capture.json']:preserve(p,str(p.relative_to(ROOT)))
  for suffix in ['cycle-events.json','live-envelope-records.bin','live-envelope-m1-records.bin']:
   p=ROOT/f'validation/tone-refresh-live/6d-ff/{region}-{suffix}';preserve(p,str(p.relative_to(ROOT)))
  for tag in ['sms','md']:
   p=ROOT/f'validation/tone-refresh-live/6d-ff/captures-{region}-{tag}/capture.json';preserve(p,str(p.relative_to(ROOT)))
  p=ROOT/f'validation/audio-tone-channel-live/6d-ff/{region}-live-envelope-records.bin';preserve(p,'reference/'+str(p.relative_to(ROOT)))
  p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/6d-ff/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['audio_tone_channel_cost_report.json','live_tone_channel_cost_report.json']:preserve(ROOT/'analysis'/name,'reference/'+name)
 for name in ['audio-tone-channel-refresh.log','build-live-tone-refresh.log','audio-live-tone-refresh-core-build.log','live-tone-refresh.log','live-tone-refresh-validation.log','generate-tone-channel-refresh.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('audio_tone_channel_refresh_report.json',20680),('live_tone_refresh_report.json',3372)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest;preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/audio_tone_channel_refresh_milestone.md','audio_tone_channel_refresh_milestone.md')
 for name in ['genesis_plus_gx_enveloperefresh_libretro.dll','genesis_plus_gx_livetonerefresh_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Tone channel M1/R evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
