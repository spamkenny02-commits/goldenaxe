"""Freeze sprite renderer/native transfer evidence before generated cleanup."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=['class0-sprite8-real','class0-sprite8-real-rgb','class0-sprite8-overflow','class0-sprite8-wrap','class0-sprite8-empty','class0-sprite8-capacity','class0-sprite8-source-proof']

def main():
 previous=ROOT/'analysis/md-psg-native-prep-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/md-z80-psg-'+v) for v in VARIANTS]+[ROOT/'validation/sms-sprite8',ROOT/'validation/md-sms-sprite8-contract',ROOT/'validation/md-sprite8-palette']
 assert all(p.is_dir() for p in roots)
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 def report(name,folder=None):
  p=ROOT/('analysis/'+name+'_report.json');raw=p.read_bytes();r=json.loads(raw);paths.add(p);reports[p.relative_to(ROOT).as_posix()]=sha(raw)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   source=ROOT/'megadrive/src'/name
   assert source.is_file() and sha(source.read_bytes())==digest,(p,name);paths.add(source)
  if folder:
   assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
   for row in r['results']:
    assert row['done']==1 and not row['failures']
    assert sha((folder/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
  return r
 for v in VARIANTS:
  r=report('md_z80_psg_'+v.replace('-','_'),ROOT/('validation/md-z80-psg-'+v))
  assert all(x['cases']==48 and x['bytes']==2976 and x['plain_core_identical'] and not x['sprite8_readback_errors'] for x in r['results'])
  if v.endswith('source-proof'):assert all(x['scene_state_checks']==768 and x['scene_readback_words']==186624 for x in r['results'])
  paths.add(ROOT/('validation/z80-psg-'+v+'-run.log'))
 host=report('sms_sprite8');assert host['cases']==701 and host['pixels_compared']==34455552
 contract=report('md_sms_sprite8_contract',roots[-2]);assert all(x['checks']==25 for x in contract['results'])
 calibration=report('md_sprite8_palette');assert sha((roots[-1]/'out/release/rom.bin').read_bytes())==calibration['kernel_sha256']
 assert sha((roots[-1]/'src/main.c').read_bytes())==calibration['source_sha256']
 physical=report('md_sms_sprite8_physical');assert len(physical['results'])==12
 assert sum(x['dma_commits'] for x in physical['results'])==42048 and sum(x['sprite_dma_commits'] for x in physical['results'])==5376
 assert all(x['private_gap_max']<17100 for x in physical['results'])
 pixels=report('md_sms_sprite8_pixel');assert len(pixels['results'])==12 and all(x['differences']==0 for x in pixels['results'])
 assert all(x['priority_hidden_pixels']>0 for x in pixels['results'] if x['case']==4)
 prior=report('md_sms_sprite8_previous_physical');assert (ROOT/'analysis/md_sms_sprite8_previous_physical_report.json').read_bytes()==(ROOT/'analysis/md_psg_native_prep_physical_report.json').read_bytes()
 paths.add(ROOT/'validation/sms-vertical-check/capture.json')
 for frame in range(3101,3161):
  for prefix in ['vram','vdp_regs']:paths.add(ROOT/f'validation/sms-vertical-check/{prefix}_{frame:05d}.bin')
 for name in ['README.md','analysis/world_next.md','analysis/md_sms_sprite8_milestone.md','validation/md-sms-sprite8-world-prefix.json',
  'tools/validate_md_z80_psg.py','tools/analyze_md_class0_scene.py','tools/md_sms_sprite8_fixture.py',
  'tools/validate_sms_sprite8.py','tools/validate_md_sms_sprite8_contract.py','tools/validate_md_sprite8_palette.py',
  'tools/validate_md_sms_sprite8_pixels.py','tools/archive_md_sms_sprite8.py','tools/archive_lossless_evidence.py',
  'tools/md_z80_source_video_fixture.py','analysis/md_psg_native_prep_physical_report.json',
  'analysis/md_z80_psg_class0_refresh_native_prep_report.json']:
  paths.add(ROOT/name)
 for name in ['source_sms_sprite8.c','source_sms_sprite8.h','md_sms_sprite8_stream.c','md_sms_sprite8_stream.h']:paths.add(ROOT/'megadrive/src'/name)
 paths.update(ROOT.glob('validation/md-sms-sprite8-*-run.log'));paths.update(ROOT.glob('validation/md-sprite8-*-run.log'))
 prefix=json.loads((ROOT/'validation/md-sms-sprite8-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 out=ROOT/'analysis/md-sms-sprite8-v0203';m=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,production_integration=False,native_actor_sat_production=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent sprite archive readback passed.')
if __name__=='__main__':main()
