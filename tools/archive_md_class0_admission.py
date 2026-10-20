"""Freeze native admission variants and source snapshots before generated cleanup."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-hidden-preflight','class0-hidden-prepared-preflight','class0-hidden-grant-control','class0-hidden-grant-stamp','class0-hidden-grant-proof']
UNITS=['hidden-preflight','hidden-prepared-age','hidden-grant']
def main():
 previous=ROOT/'analysis/md-class0-hidden-scheduling-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS]+[ROOT/('validation/md-video-span-contract-'+v) for v in UNITS]
 assert all(p.is_dir() for p in roots)
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={};snapshots=[p for d in roots for p in d.glob('*.snapshot')]
 def report(path,folder=None):
  raw=path.read_bytes();r=json.loads(raw);paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(raw)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   source=next((p for p in [ROOT/'megadrive/src'/name]+snapshots if p.is_file() and sha(p.read_bytes())==digest),None)
   assert source,(path,name,digest);paths.add(source)
  if folder:
   assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
   for row in r['results']:
    assert not row['failures']
    assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  return r
 for v in VARIANTS:
  report(ROOT/('analysis/md_z80_psg_'+v.replace('-','_')+'_report.json'),ROOT/('validation/md-z80-psg-'+v))
  paths.update(ROOT.glob('validation/z80-psg-'+v+'-*.log'))
 for v in UNITS:
  report(ROOT/('analysis/md_video_span_contract_'+v.replace('-','_')+'_report.json'),ROOT/('validation/md-video-span-contract-'+v))
  paths.add(ROOT/('validation/md-video-span-contract-'+v+'-run.log'))
 physical=report(ROOT/'analysis/md_class0_admission_physical_report.json')
 assert len(physical['results'])==10 and sum(x['dma_commits'] for x in physical['results'])==35040
 assert all(x['private_gap_max']<17100 for x in physical['results'])
 for row in physical['results']:
  if row['variant'] in ('class0-hidden-grant-stamp','class0-hidden-grant-proof'):
   covered=set(v for entry in row['rows'] for v in entry['successful_guard_raw_v'])
   assert len(covered)==250 and {0,127,128,255}.issubset(covered)
 for name in ['analysis/md_class0_admission_baseline_physical_report.json','analysis/md_class0_admission_comparison_report.json',
  'analysis/md_class0_preflight_physical_report.json','analysis/md_class0_admission_milestone.md','analysis/world_next.md','README.md',
  'megadrive/src/md_z80_video_span.c','megadrive/src/md_z80_video_span.h','tools/analyze_md_class0_scene.py',
  'tools/validate_md_video_span_contract.py','tools/validate_md_z80_psg.py','tools/compare_md_class0_admission.py',
  'tools/archive_md_class0_admission.py','tools/archive_lossless_evidence.py','validation/md-class0-admission-world-prefix.json']:
  paths.add(ROOT/name)
 paths.update(ROOT.glob('validation/md-class0-admission-*-run.log'))
 prefix=json.loads((ROOT/'validation/md-class0-admission-world-prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,
  rejected_preflight=VARIANTS[:2],experimental_candidate='class0-hidden-grant-stamp',full_proof='class0-hidden-grant-proof',
  default_changed=False,production_integration=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False)
 out=ROOT/'analysis/md-class0-admission-v0203';manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
  raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent admission archive readback passed.')
if __name__=='__main__':main()
