"""Freeze autonomous v0218 publication/scroll/intro evidence before cleanup."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 previous=ROOT/'analysis/playable-sprite-limit-v0210/manifest.json';old=json.loads(previous.read_bytes());release=ROOT/'analysis/world_publication_v0218_report.json';r=json.loads(release.read_bytes());recovery=ROOT/'analysis/world_publication_recovery_v0218_report.json';rr=json.loads(recovery.read_bytes());assert r['passed'] and rr['passed'] and rr['rgb_pixels_recovered']==614400 and rr['source_published_steps_recovered']==80
 names=['md-sprite-publish-observer','md-sprite-publish','md-sprite-publish_ntsc','sms-scroll-cadence','start-menu-sfx']
 for version in [215,216,217,218]:names.extend(['playable-sprite-end-v'+str(version).zfill(4),'world-frame-coherence-v'+str(version).zfill(4),'playable-sprite-limit-v'+str(version).zfill(4),'world-publish-regression-v'+str(version).zfill(4)])
 names.extend(tag+'-intro-natural'+suffix for tag in ['md','sms'] for suffix in ['', '-pal'])
 names.extend('inventory-restore-'+place+'-'+region+'-'+tag for place in ['exterior','first_house','second_house'] for region in ['auto','pal'] for tag in ['md','sms'])
 roots=[ROOT/('validation/'+n) for n in names if (ROOT/('validation/'+n)).exists()];paths=set(p for folder in roots for p in folder.rglob('*') if p.is_file())
 for name,digest in r['reports'].items():
  path=ROOT/name;assert sha(path.read_bytes())==digest;paths.add(path)
 for name,digest in r['sources'].items():
  path=ROOT/name;assert sha(path.read_bytes())==digest;paths.add(path)
 for name in ['README.md','analysis/world_next.md','analysis/world_publication_v0218.md','analysis/world_publication_v0218_report.json','analysis/world_publication_recovery_v0218_report.json','analysis/playable_sprite_end_wip.md','validation/world-publication-v0218-world-prefix.json','validation/v0210-symbols.txt','megadrive/src/actors.h','megadrive/out/release/symbol.txt','megadrive/out/release/rom.bin','build.ps1','gaw-megadrive.bin','gaw-title-megadrive.bin','versions/index.json','versions/README.md','tools/archive_world_publication_release.py','tools/archive_lossless_evidence.py','tools/summarize_world_publication_release.py','tools/verify_world_publication_release.py','tools/build_sprite_publish_core.py','tools/build_timing_core.py','tools/observe_sprite_publish.py','tools/observe_source_scroll_cadence.py','tools/validate_world_publish_regression.py','tools/validate_world_frame_coherence.py','tools/validate_playable_sprite_end.py','tools/validate_playable_sprite_limit.py','tools/validate_intro.py','tools/validate_inventory_restore.py','tools/validate_start_menu_sfx.py','tools/run_core.py','tools/version_rom.py','tools/update_readme.py','validation/sms-vertical-check/ram_03120.bin','validation/sms-vertical-check/capture.json']:
  paths.add(ROOT/name)
 for pattern in ['playable_sprite_end_v02*_report.json','playable_sprite_limit_v02*_report.json','world_frame_coherence_v02*_report.json','world_publish_regression_v02*_report.json']:
  paths.update((ROOT/'analysis').glob(pattern))
 paths.update(ROOT.glob('validation/v02*.log'))
 for version in range(211,219):
  for folder in (ROOT/'versions').glob('v'+str(version).zfill(4)+'-*'):paths.update(p for p in folder.iterdir() if p.is_file())
 prefix=json.loads((ROOT/'validation/world-publication-v0218-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==r['md_sha256']
 assert len(list((ROOT/'versions').glob('*/*.bin')))==218
 engine=ROOT.parents[1]/'work/genesis-plus-gx';build=json.loads((ROOT/'validation/md-sprite-publish-observer/build.json').read_bytes());assert build['restored'] and sha((engine/'core/vdp_ctrl.c').read_bytes())==build['original_sha256']
 cadence=json.loads((ROOT/'analysis/source_scroll_cadence_report.json').read_bytes());assert cadence['restored'] and sha((engine/'core/z80/z80.c').read_bytes())==cadence['original_source_sha256']
 assert sha((engine/'genesis_plus_gx_z80_psg_io_libretro.dll').read_bytes())=='6c1b76eaec069abf1dca3b82affb1a9116605567847b9bfcd4bf4bb8b572c830'
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 out=ROOT/'analysis/world-publication-v0218';m=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),previous_playable_sha256=old['playable_sha256'],playable_sha256=r['md_sha256'],numbered_roms_preserved=218,production_world_vblank_publication=True,source_vertical_cadence_verified=True,full_game_validated=False,source_rng_faithful=False,hardware_console_validated=False,waveform_validated=False),roots,'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent v0218 archive full readback passed.')
if __name__=='__main__':main()
