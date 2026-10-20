"""Freeze display-off class0 evidence, verify fully, then clean generated files."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-hidden-readback','class0-hidden-proof','class0-hidden-production']
def main():
 previous=ROOT/'analysis/md-class0-scene-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS]
 roots += [ROOT/'validation/md-class0-stream-contract-hidden',ROOT/'validation/md-video-span-contract-hidden']
 assert all(p.is_dir() for p in roots)
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 def report(path,folder=None):
  raw=path.read_bytes();r=json.loads(raw);reports[path.relative_to(ROOT).as_posix()]=sha(raw);paths.add(path)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   source=ROOT/'megadrive/src'/name;assert sha(source.read_bytes())==digest,(path,name);paths.add(source)
  if folder:
   assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
   for row in r['results']:
    assert row['failures']==0
    assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  return r
 for v in VARIANTS:
  report(ROOT/('analysis/md_z80_psg_'+v.replace('-','_')+'_report.json'),ROOT/('validation/md-z80-psg-'+v))
  paths.update(ROOT.glob('validation/z80-psg-'+v+'-*.log'))
 for name in ['md_class0_stream_contract_hidden','md_video_span_contract_hidden']:
  report(ROOT/('analysis/'+name+'_report.json'),ROOT/('validation/'+name.replace('_','-')))
 physical=report(ROOT/'analysis/md_class0_hidden_physical_report.json')
 assert len(physical['results'])==6 and sum(r['dma_commits'] for r in physical['results'])==21024
 assert all(r['hidden'] and r['private_gap_max']<17100 for r in physical['results'])
 assert (ROOT/'analysis/md_class0_scene_physical_report.json').read_bytes()==(ROOT/'analysis/md_class0_scene_physical_regression_report.json').read_bytes()
 for name in ['README.md','analysis/world_next.md','analysis/md_class0_hidden_milestone.md',
  'analysis/md_class0_scene_physical_regression_report.json','tools/analyze_md_class0_scene.py',
  'tools/md_class0_scene_fixture.py','tools/validate_md_class0_stream_contract.py',
  'tools/validate_md_video_span_contract.py','tools/validate_md_z80_psg.py',
  'tools/archive_md_class0_hidden.py','tools/archive_lossless_evidence.py',
  'validation/md-class0-hidden-world-prefix.json','validation/md-class0-stream-contract-hidden-run.log',
  'validation/md-video-span-contract-hidden-run.log']:
  paths.add(ROOT/name)
 prefix=json.loads((ROOT/'validation/md-class0-hidden-world-prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:
  assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,
  selected_kernels=VARIANTS,production_integration=False,sprites=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False)
 out=ROOT/'analysis/md-class0-hidden-v0203';manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
  raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent hidden scene archive readback passed.')
if __name__=='__main__':main()
