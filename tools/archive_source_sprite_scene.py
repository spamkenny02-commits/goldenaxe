"""Archive native actor SAT production and connected rendering evidence."""
from pathlib import Path
import gzip,json,sys
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 previous=ROOT/'analysis/md-sms-sprite8-v0203/manifest.json';old=json.loads(previous.read_bytes())
 roots=[ROOT/'validation/source-sprite-scene',ROOT/'validation/source-sprite-scene-68k',ROOT/'validation/md-z80-psg-class0-sprite8-actors']
 paths=set(p for d in roots for p in d.rglob('*') if p.is_file());reports={}
 def report(name):
  p=ROOT/('analysis/'+name+'_report.json');raw=p.read_bytes();r=json.loads(raw);paths.add(p);reports[p.relative_to(ROOT).as_posix()]=sha(raw)
  for name,digest in {**r.get('sources',{}),**r.get('headers',{})}.items():
   s=ROOT/'megadrive/src'/name;assert sha(s.read_bytes())==digest,(p,name);paths.add(s)
  return r
 source=report('source_sprite_scene');native=report('source_sprite_scene_68k');live=report('md_z80_psg_class0_sprite8_actors');pixels=report('md_sprite_scene_pixel');physical=report('md_sprite_scene_physical')
 for kind in ['physical','pixel']:
  report('md_sprite_scene_previous_'+kind)
  assert (ROOT/f'analysis/md_sprite_scene_previous_{kind}_report.json').read_bytes()==(ROOT/f'analysis/md_sms_sprite8_{kind}_report.json').read_bytes()
 assert len(source['cases'])==133 and source['invalid_atomic_checks']==7
 assert all(r['cases']==133 for r in source['results'])
 assert all(r['checks']==133 and not r['failures'] for r in native['results'])
 assert native['source_report_sha256']==reports['analysis/source_sprite_scene_report.json']
 assert sha((roots[0]/'source-fixture.sms').read_bytes())==source['fixture_sha256']
 for row in source['results']:assert sha((roots[0]/(row['region']+'-records.bin')).read_bytes())==row['records_sha256']
 for folder,r in [(roots[1],native),(roots[2],live)]:assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
 assert all(r['sprite8_builds']==48 and r['scene_state_checks']==768 and r['scene_readback_words']==186624 and r['sprite8_readback_words']==27648 and not r['failures'] and r['plain_core_identical'] for r in live['results'])
 for row in live['results']:assert sha((roots[2]/(row['region']+'-events.json')).read_bytes())==row['events_sha256']
 assert len(pixels['results'])==len(physical['results'])==2
 assert all(r['differences']==0 and r['painted_sprite_pixels']==833 for r in pixels['results'])
 assert sum(r['dma_commits'] for r in physical['results'])==7008 and sum(r['sprite_dma_commits'] for r in physical['results'])==864
 assert all(r['private_gap_max']<17100 for r in physical['results'])
 for name in ['README.md','analysis/world_next.md','analysis/source_sprite_scene_milestone.md','validation/md-sprite-scene-world-prefix.json',
  'megadrive/src/source_sprite_scene.c','megadrive/src/source_sprite_scene.h',
  'tools/validate_source_sprite_scene.py','tools/validate_source_sprite_scene_68k.py','tools/md_sms_sprite8_fixture.py',
  'tools/validate_md_z80_psg.py','tools/validate_md_sms_sprite8_pixels.py','tools/analyze_md_class0_scene.py',
  'tools/sprite_reference.py','tools/archive_source_sprite_scene.py','tools/archive_lossless_evidence.py',
  'validation/source-sprite-scene-run.log','validation/source-sprite-scene-68k-run.log',
  'validation/z80-psg-class0-sprite8-actors-run.log','validation/md-sprite-scene-pixel-run.log','validation/md-sprite-scene-physical-run.log',
  'validation/sms-vertical-check/capture.json','analysis/bank_00.asm']:
  paths.add(ROOT/name)
 for f in range(3101,3161):paths.add(ROOT/f'validation/sms-vertical-check/ram_{f:05d}.bin')
 paths.update(ROOT.glob('validation/md-sprite-scene-*-run.log'))
 for prefix in ['vram','vdp_regs']:paths.add(ROOT/f'validation/sms-vertical-check/{prefix}_03120.bin')
 prefix=json.loads((ROOT/'validation/md-sprite-scene-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())==source['source_rom_sha256']=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 out=ROOT/'analysis/md-sprite-scene-v0203';m=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,actor_sat_fixture_connected=True,production_integration=False,source_instruction_irq_boundaries=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent actor SAT archive readback passed.')
if __name__=='__main__':main()
