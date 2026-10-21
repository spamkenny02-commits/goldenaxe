"""Freeze native sprite/wait/original-IRQ composition before generated cleanup."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 previous=ROOT/'analysis/sprite-scene-timed-v0203/manifest.json';old=json.loads(previous.read_bytes());roots=[ROOT/('validation/'+n) for n in ['game-sprite-frame','game-sprite-frame-68k','game-sprite-frame-observer']]
 engine=ROOT.parents[1]/'work/genesis-plus-gx';build=json.loads((roots[2]/'build.json').read_bytes());assert build['restored']
 for file,path in [('z80.c',engine/'core/z80/z80.c'),('memz80.c',engine/'core/memz80.c')]:
  raw=path.read_bytes();assert sha(raw)==build['original_sha256'][file];(roots[2]/(file+'.original')).write_bytes(raw)
 dll=engine/'genesis_plus_gx_game_sprite_frame_libretro.dll';assert sha(dll.read_bytes())==build['core_sha256'];(roots[2]/'observer.dll').write_bytes(dll.read_bytes())
 assert sha((engine/'genesis_plus_gx_z80_psg_io_libretro.dll').read_bytes())=='6c1b76eaec069abf1dca3b82affb1a9116605567847b9bfcd4bf4bb8b572c830'
 paths=set(p for root in roots for p in root.rglob('*') if p.is_file());reports={}
 def report(name):
  path=ROOT/('analysis/'+name+'_report.json');b=path.read_bytes();r=json.loads(b);paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(b)
  for name,digest in r.get('sources',{}).items():
   p=ROOT/'megadrive/src'/name;assert sha(p.read_bytes())==digest;paths.add(p)
  return r
 source=report('game_sprite_frame');native=report('game_sprite_frame_68k');assets=report('game_sprite_frame_assets')
 assert len(source['cases'])==266 and source['trace_disabled_full_ram_clock_agree'] and source['contract_checks_per_region']==native['contract_checks_per_region']==5
 assert native['source_report_sha256']==sha((ROOT/'analysis/game_sprite_frame_report.json').read_bytes())
 assert sha((roots[0]/'source-fixture.sms').read_bytes())==source['fixture_sha256']
 assert sha((roots[1]/'out/release/rom.bin').read_bytes())==native['kernel_sha256']
 for row in source['results']:
  assert row['cases']==133
  for kind in ['points','ports']:assert sha((roots[0]/(row['region']+'-'+kind+'.bin')).read_bytes())==row[kind+'_sha256']
 assert all(r['done'] and not r['failures'] and r['checks']==133 and r['irqs']==217 and r['sat']==133 and r['psg']==592 for r in native['results'])
 assert len(assets['results'])==2 and all(r['cases']==133 and r['checkpoints']==532 and r['irq_inputs']==217 and r['port_values_dates']==26128 for r in assets['results'])
 for name in ['README.md','analysis/world_next.md','analysis/game_sprite_frame_milestone.md','validation/game-sprite-frame-world-prefix.json',
  'tools/game_sprite_frame_fixture.py','tools/build_game_sprite_frame_core.py','tools/build_timing_core.py','tools/validate_game_sprite_frame.py',
  'tools/validate_game_sprite_frame_68k.py','tools/verify_game_sprite_frame_assets.py','tools/validate_source_sprite_scene.py',
  'tools/validate_sprite_scene_timed.py','tools/validate_native_audio_reader.py','tools/actor_reference.py','tools/run_core.py',
  'tools/archive_game_sprite_frame.py','tools/archive_lossless_evidence.py','analysis/bank_00.asm','validation/sms-vertical-check/capture.json']:
  paths.add(ROOT/name)
 paths.update(ROOT.glob('validation/game-sprite-frame*-run.log'))
 for n in range(3101,3161):paths.add(ROOT/f'validation/sms-vertical-check/ram_{n:05d}.bin')
 prefix=json.loads((ROOT/'validation/game-sprite-frame-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert sha((ROOT/'input/original.sms').read_bytes())==source['source_rom_sha256']
 roms=list((ROOT/'versions').glob('*/*.bin'));assert len(roms)==207
 out=ROOT/'analysis/game-sprite-frame-v0203';manifest=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,numbered_roms_preserved=len(roms),native_sprite_wait_full_irq_audio_composed=True,hardware_status_supplied=True,production_integration=False,video_frame_deadlines_accepted=False,audio_waveform_validated=False),roots,'--cleanup' in sys.argv)
 for item in manifest['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent game frame archive readback passed.')
if __name__=='__main__':main()
