"""Archive accepted measurements and rejected scheduling prototypes losslessly."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-hidden-delivery','class0-hidden-batch64','class0-hidden-slack64-owned','class0-hidden-sequence-backoff','class0-hidden-repeat-batches']
def main():
 previous=ROOT/'analysis/md-class0-hidden-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS+['class0-hidden-slack64']]
 assert all(p.is_dir() for p in roots)
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 for v in VARIANTS:
  p=ROOT/('analysis/md_z80_psg_'+v.replace('-','_')+'_report.json');raw=p.read_bytes();r=json.loads(raw);paths.add(p);reports[p.relative_to(ROOT).as_posix()]=sha(raw)
  folder=ROOT/('validation/md-z80-psg-'+v)
  assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
  for row in r['results']:
   assert not row['failures'] and row['cases']==48
   assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  for name,digest in {**r['sources'],**r['headers']}.items():
   source=ROOT/'megadrive/src'/name;assert sha(source.read_bytes())==digest;paths.add(source)
 physical=json.loads((ROOT/'analysis/md_class0_hidden_scheduling_physical_report.json').read_bytes())
 assert len(physical['results'])==10 and sum(x['dma_commits'] for x in physical['results'])==35040
 assert all(x['private_gap_max']<17100 for x in physical['results'])
 failed=json.loads((ROOT/'analysis/md_class0_hidden_slack_shared_failure_report.json').read_bytes());folder=roots[-1]
 assert not failed['passed'] and failed['failure_code']==1025
 assert sha((folder/'out/release/rom.bin').read_bytes())==failed['kernel_sha256']
 assert sha((folder/'ntsc-events.json').read_bytes())==failed['events_sha256']
 for v in VARIANTS+['class0-hidden-slack64']:paths.update(ROOT.glob('validation/z80-psg-'+v+'-*.log'))
 paths.update(ROOT.glob('analysis/md_class0_hidden_*physical_report.json'))
 for name in ['analysis/md_class0_hidden_scheduling_comparison_report.json','analysis/md_class0_scheduling_default_regression_report.json',
  'analysis/md_class0_hidden_slack_shared_failure_report.json','analysis/md_class0_scheduling_milestone.md',
  'analysis/world_next.md','README.md','tools/md_class0_scene_fixture.py','tools/md_clock_service_kernel.py',
  'tools/validate_md_z80_psg.py','tools/analyze_md_class0_scene.py','tools/archive_md_class0_scheduling.py',
  'tools/archive_lossless_evidence.py','validation/md-class0-scheduling-world-prefix.json']:
  paths.add(ROOT/name)
 prefix=json.loads((ROOT/'validation/md-class0-scheduling-world-prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,
  not_promoted=VARIANTS,rejected_shared_clock='class0-hidden-slack64',default_options_changed=False,production_integration=False,
  video_frame_deadlines_accepted=False,audio_waveform_validated=False)
 out=ROOT/'analysis/md-class0-hidden-scheduling-v0203';manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
  raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent scheduling archive readback passed.')
if __name__=='__main__':main()
