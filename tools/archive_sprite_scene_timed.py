"""Freeze source/native instruction boundaries and controlled SAT IRQ evidence."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 previous=ROOT/'analysis/md-sprite-scene-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/('validation/'+name) for name in ['sprite-scene-observer','sprite-scene-timed','sprite-scene-timed-irq','sprite-scene-timed-68k','sprite-scene-timed-irq-68k','sprite-scene-observer-parity']]
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 def report(name):
  p=ROOT/('analysis/'+name+'_report.json');raw=p.read_bytes();r=json.loads(raw);paths.add(p);reports[p.relative_to(ROOT).as_posix()]=sha(raw)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   source=ROOT/'megadrive/src'/name;assert sha(source.read_bytes())==digest,(p,name);paths.add(source)
  return r
 for suffix in ['','_irq']:
  source=report('sprite_scene_timed'+suffix);native=report('sprite_scene_timed'+suffix+'_68k');folder=ROOT/('validation/sprite-scene-timed'+suffix.replace('_','-'))
  assert len(source['cases'])==266 and len(source['results'])==len(native['results'])==2
  assert sum(x['irq_count'] for x in source['cases'])==(168 if suffix else 0)
  assert native['source_report_sha256']==reports['analysis/sprite_scene_timed'+suffix+'_report.json']
  assert sha((folder/'source-fixture.sms').read_bytes())==source['fixture_sha256']
  assert sha((ROOT/('validation/sprite-scene-timed'+suffix.replace('_','-')+'-68k/out/release/rom.bin')).read_bytes())==native['kernel_sha256']
  for row in source['results']:assert row['instructions']==110010 and sha((folder/(row['region']+'-records.bin')).read_bytes())==row['records_sha256']
  assert all(x['done'] and x['checks']==133 and x['points']==110143 and not x['failures'] and x['irqs']==(84 if suffix else 0) for x in native['results'])
 parity=report('sprite_scene_observer_parity');assert parity['previous_fixture_generator_identical'] and len(parity['results'])==4
 assert all(x['plain_core_same'] and x['partial_sat_snapshots']==(10 if x['interrupts'] else 0) for x in parity['results'])
 codec=report('sprite_scene_trace_codec');assert len(codec['results'])==4 and all(x['points']==110143 and x['ram_bytes_per_point']==581 for x in codec['results'])
 build=json.loads((roots[0]/'build.json').read_bytes());assert build['source_restored']
 core=ROOT.parents[1]/'work/genesis-plus-gx';assert sha((core/'core/z80/z80.c').read_bytes())==build['original_source_sha256']
 assert sha((roots[0]/'observer.dll').read_bytes())==build['core_sha256']
 for name in ['README.md','analysis/world_next.md','analysis/sprite_scene_timed_milestone.md','validation/sprite-scene-timed-world-prefix.json',
  'tools/build_sprite_scene_core.py','tools/build_timing_core.py','tools/validate_source_sprite_scene.py','tools/validate_sprite_scene_timed.py',
  'tools/validate_sprite_scene_timed_68k.py','tools/validate_sprite_scene_observer_parity.py','tools/verify_sprite_scene_trace_codec.py',
  'tools/archive_sprite_scene_timed.py','tools/archive_lossless_evidence.py','analysis/bank_00.asm','validation/sms-vertical-check/capture.json']:
  paths.add(ROOT/name)
 paths.update(ROOT.glob('validation/sprite-scene-*-run.log'))
 for n in range(3101,3161):paths.add(ROOT/f'validation/sms-vertical-check/ram_{n:05d}.bin')
 prefix=json.loads((ROOT/'validation/sprite-scene-timed-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 out=ROOT/'analysis/sprite-scene-timed-v0203';m=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,instruction_boundary_source_native_verified=True,controlled_irq_snapshots_verified=True,original_game_irq_sat_publication=False,production_integration=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent timed sprite archive readback passed.')
if __name__=='__main__':main()
