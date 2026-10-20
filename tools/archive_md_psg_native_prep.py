"""Freeze selected native PSG preparation, model checks and paired native evidence."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-grant-native-prep','class0-refresh-native-prep','class0-refresh-native-prep-proof']
def main():
 previous=ROOT/'analysis/md-class0-admission-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS]+[ROOT/'validation/md-z80-bridge-native-prep',ROOT/'validation/md-z80-polled-native-prep',ROOT/'validation/md-psg-native-prep-control']
 assert all(p.is_dir() for p in roots)
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());snapshots=[p for d in roots for p in d.glob('*.snapshot')];reports={}
 def report(path,folder=None):
  raw=path.read_bytes();r=json.loads(raw);paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(raw)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   source=next((p for p in [ROOT/'megadrive/src'/name]+snapshots if p.is_file() and sha(p.read_bytes())==digest),None)
   assert source,(path,name,digest);paths.add(source)
  if folder:
   assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
   for row in r['results']:
    assert row['cases']==48 and not row['failures']
    assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  return r
 for v in VARIANTS:
  report(ROOT/('analysis/md_z80_psg_'+v.replace('-','_')+'_report.json'),ROOT/('validation/md-z80-psg-'+v))
  paths.add(ROOT/('validation/z80-psg-'+v+'-run.log'))
 for name in ['md_z80_bridge_native_prep','md_z80_polled_native_prep']:report(ROOT/('analysis/'+name+'_report.json'))
 physical=report(ROOT/'analysis/md_psg_native_prep_physical_report.json');assert len(physical['results'])==6 and sum(r['dma_commits'] for r in physical['results'])==21024
 assert all(r['private_gap_max']<17100 for r in physical['results'])
 codegen=report(ROOT/'analysis/md_psg_native_prep_codegen_report.json');assert codegen['legacy_control_identical'] and len(codegen['results'])==3
 assert sha((roots[-1]/'out/release/rom.bin').read_bytes())==codegen['legacy_control_kernel_sha256']
 comparison=report(ROOT/'analysis/md_psg_native_prep_comparison_report.json');assert comparison['selected_source_default'] and comparison['host_descriptor_checks']==12016 and comparison['host_polled_checks']==132
 for name in ['README.md','analysis/world_next.md','analysis/md_psg_native_prep_milestone.md','megadrive/src/md_z80_psg.c',
  'tools/validate_md_z80_bridge.py','tools/validate_md_z80_polled.py','tools/validate_md_z80_psg.py',
  'tools/verify_md_psg_prep_codegen.py','tools/compare_md_psg_native_prep.py','tools/archive_md_psg_native_prep.py',
  'tools/archive_lossless_evidence.py','tools/analyze_md_class0_scene.py','validation/md-psg-native-prep-world-prefix.json',
  'validation/md-z80-bridge-native-prep-run.log','validation/md-z80-polled-native-prep-run.log']:
  paths.add(ROOT/name)
 paths.update(ROOT.glob('validation/md-psg-native-prep-*-run.log'))
 prefix=json.loads((ROOT/'validation/md-psg-native-prep-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 metadata=dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,
  native_preparation_selected=True,fresh_grant_video_selected=False,production_integration=False,
  video_frame_deadlines_accepted=False,audio_waveform_validated=False)
 out=ROOT/'analysis/md-psg-native-prep-v0203';manifest=freeze(ROOT,out,paths,metadata,roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
  raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent native preparation archive readback passed.')
if __name__=='__main__':main()
