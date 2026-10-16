"""Archive complete8000 M1/R composition,gate fixture and24 live route captures."""
import ast,hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/audio-reader-refresh-research-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file():assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes(),('production changed',p.name)
 pending=['audio_reader_refresh','validate_audio_reader_refresh','validate_live_reader_refresh','build_live_reader_refresh_core','profile_paid_passage_loader_phases','validate_audio_reader_gates_cost','archive_audio_reader_refresh_research'];seen=set()
 while pending:
  name=pending.pop();path=ROOT/'tools'/f'{name}.py'
  if name in seen or not path.exists():continue
  seen.add(name);preserve(path,'tools/'+path.name)
  for node in ast.walk(ast.parse(path.read_text())):
   if isinstance(node,ast.ImportFrom) and node.module:pending.append(node.module.split('.')[0])
   elif isinstance(node,ast.Import):pending.extend(alias.name.split('.')[0] for alias in node.names)
 preserve(ROOT/'analysis/audio-reader-refresh-live-v0183/z80-live-reader-refresh.txt','z80-live-reader-refresh.txt');preserve(ROOT/'analysis/audio-envelope-refresh-v0183/z80-envelope-refresh.txt','z80-envelope-refresh.txt');preserve(ROOT/'analysis/bank_06.asm','reference/bank_06.asm')
 base=ROOT/'validation/audio-reader-refresh/gates';preserve(base/'source.sms',str((base/'source.sms').relative_to(ROOT)))
 for region in ['auto','pal']:
  for p in [base/f'{region}-results.bin',base/region/'capture.json']:preserve(p,str(p.relative_to(ROOT)))
 preserve(ROOT/'analysis/audio_reader_gates_cost_report.json','reference/audio_reader_gates_cost_report.json');preserve(ROOT/'analysis/paid_passage_reference.json','reference/paid_passage_reference.json')
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
 for town,*_ in routes:
  for mask in [0,255]:
   for region in ['auto','pal']:
    root=ROOT/f'validation/reader-refresh-live/{town:02x}-{mask:02x}'
    for suffix in ['cycle-events.json','audio-irq-events.json','live-envelope-records.bin','live-envelope-m1-records.bin']:
     p=root/f'{region}-{suffix}';preserve(p,str(p.relative_to(ROOT)))
    for tag in ['sms','md']:
     p=root/f'captures-{region}-{tag}/capture.json';preserve(p,str(p.relative_to(ROOT)))
    p=ROOT/f'validation/wait-raster/{town:02x}-{mask:02x}/{region}-live-envelope-records.bin';preserve(p,'reference/'+str(p.relative_to(ROOT)))
    p=ROOT/f'versions/v0179-d018ed93/validation/paid-exit-music/{town:02x}-{mask:02x}/{region}-cycle-events.json';preserve(p,'reference/'+str(p.relative_to(ROOT)))
 for name in ['audio-reader-refresh.log','build-live-reader-refresh.log','audio-live-reader-refresh-core-build.log','live-reader-refresh.log','live-reader-refresh-group1.log','live-reader-refresh-group2.log','live-reader-refresh-group3.log','live-reader-refresh-validation.log']:preserve(ROOT/'validation'/name,'logs/'+name)
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for name,count in [('audio_reader_refresh_report.json',10752),('live_audio_reader_refresh_report.json',24)]:
  report=json.loads((ROOT/'analysis'/name).read_text());assert report['cases']==count and report['md_sha256']==digest
  if count==24:assert report['reader_calls']==14424 and all(r['cases']==601 for r in report['rows'])
  preserve(ROOT/'analysis'/name,name)
 preserve(ROOT/'analysis/audio_reader_refresh_milestone.md','audio_reader_refresh_milestone.md')
 for name in ['genesis_plus_gx_enveloperefresh_libretro.dll','genesis_plus_gx_livereaderrefresh_libretro.dll']:preserve(ROOT.parents[1]/'work/genesis-plus-gx'/name,name)
 data=(json.dumps(dict(md_sha256=digest,source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Full audio reader M1/R evidence archived and verified:',len(items),'files')
if __name__=='__main__':main()
