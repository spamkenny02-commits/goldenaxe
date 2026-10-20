"""Freeze scene pipeline evidence, including memory/window failures, before cleanup."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-scene-stream','class0-scene-stream-live','class0-scene-stream-proof',
 'class0-scene-native-palette','class0-scene-palette-proof','class0-scene-palette-native',
 'class0-scene-bounded-proof','class0-scene-bounded-native','class0-scene-production']
def main():
 previous=ROOT/'analysis/md-z80-source-phases-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS]
 units=['','-palette','-bounded'];roots += [ROOT/('validation/md-class0-stream-contract'+v) for v in units]
 assert all(p.is_dir() for p in roots);paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 snapshots=[p for d in roots for p in d.glob('*.snapshot')]
 def report(path,folder=None):
  raw=path.read_bytes();r=json.loads(raw);reports[path.relative_to(ROOT).as_posix()]=sha(raw);paths.add(path)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   current=ROOT/'megadrive/src'/name
   match=next((p for p in [current]+snapshots if p.is_file() and sha(p.read_bytes())==digest),None)
   assert match,(path,name,digest);paths.add(match)
  if folder:
   assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
   for row in r['results']:assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  return r
 for v in VARIANTS:
  p=ROOT/('analysis/md_z80_psg_'+v.replace('-','_')+'_report.json')
  if p.exists():report(p,ROOT/('validation/md-z80-psg-'+v))
  paths.update(ROOT.glob('validation/z80-psg-'+v+'-*.log'))
 for v in units:report(ROOT/('analysis/md_class0_stream_contract'+v.replace('-','_')+'_report.json'),ROOT/('validation/md-class0-stream-contract'+v))
 physical=report(ROOT/'analysis/md_class0_scene_physical_report.json');assert len(physical['results'])==6 and sum(r['dma_commits'] for r in physical['results'])==21024
 for row in physical['results']:assert row['private_gap_max']<17100
 for name in ['README.md','analysis/world_next.md','analysis/md_class0_scene_milestone.md',
  'megadrive/src/md_class0_video_stream.c','megadrive/src/md_class0_video_stream.h',
  'megadrive/src/source_class0_video.c','megadrive/src/source_class0_video.h','megadrive/src/source_class0_video_assets_generated.h',
  'tools/md_class0_scene_fixture.py','tools/validate_md_class0_stream_contract.py','tools/validate_md_z80_psg.py',
  'tools/analyze_md_class0_scene.py','tools/archive_md_class0_scene.py','tools/archive_lossless_evidence.py',
  'validation/md-class0-scene-world-prefix.json','validation/md-class0-scene-physical-run.log',
  'validation/md-class0-scene-physical-bounded-run.log']:
  paths.add(ROOT/name)
 for v in units:paths.add(ROOT/('validation/md-class0-stream-contract'+v+'-run.log'))
 prefix=json.loads((ROOT/'validation/md-class0-scene-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,
  selected_kernels=['class0-scene-bounded-proof','class0-scene-bounded-native','class0-scene-production'],
  rejected_boot='class0-scene-stream',retired_late_palette_window=['class0-scene-palette-proof','class0-scene-palette-native'],
  production_integration=False,sprites=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False)
 out=ROOT/'analysis/md-class0-scene-v0203';manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent scene archive readback passed.')
if __name__=='__main__':main()
