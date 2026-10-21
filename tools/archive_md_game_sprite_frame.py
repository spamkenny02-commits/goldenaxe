"""Freeze IRQ-driven physical sprite DMA and VRAM evidence before cleanup."""
import gzip,json,sys
from pathlib import Path
from archive_lossless_evidence import freeze,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
 previous=ROOT/'analysis/game-sprite-frame-v0203/manifest.json';old=json.loads(previous.read_bytes());folder=ROOT/'validation/md-game-sprite-frame';paths=set(p for p in folder.rglob('*') if p.is_file());reports={}
 def report(name):
  path=ROOT/('analysis/'+name+'_report.json');b=path.read_bytes();r=json.loads(b);paths.add(path);reports[path.relative_to(ROOT).as_posix()]=sha(b)
  for n,digest in r.get('sources',{}).items():
   source=ROOT/'megadrive/src'/n;assert sha(source.read_bytes())==digest;paths.add(source)
  return r
 r=report('md_game_sprite_frame');recovery=report('md_game_sprite_frame_recovery');assert r['source_report_sha256']==sha((ROOT/'analysis/game_sprite_frame_report.json').read_bytes())
 assert sha((folder/'out/release/rom.bin').read_bytes())==r['kernel_sha256']
 assert len(r['results'])==len(recovery['results'])==2
 for row in r['results']:
  assert row['done'] and row['checks']==row['published']==len(row['cases'])==133 and not row['failures'] and not row['video_errors']
  assert row['video_contracts']==5 and row['video_jobs']==1132 and row['video_words']==71936 and row['video_waits']>0
 for row in recovery['results']:assert row['cases']==133 and row['pixels_compared']==6537216
 for name in ['README.md','analysis/world_next.md','analysis/md_game_sprite_frame_milestone.md','validation/md-game-sprite-frame-world-prefix.json',
  'tools/validate_md_game_sprite_frame.py','tools/verify_md_game_sprite_frame.py','tools/archive_md_game_sprite_frame.py','tools/archive_lossless_evidence.py',
  'tools/validate_game_sprite_frame.py','tools/validate_game_sprite_frame_68k.py','tools/verify_game_sprite_frame_assets.py',
  'tools/md_sms_sprite8_fixture.py','tools/md_z80_source_video_fixture.py','tools/validate_sms_sprite8.py','tools/run_core.py',
  'megadrive/z80/md_psg_refresh_z80.asm','validation/md-game-sprite-frame-run.log','validation/sms-vertical-check/capture.json',
  'validation/sms-vertical-check/vram_03120.bin','validation/sms-vertical-check/vdp_regs_03120.bin']:
  paths.add(ROOT/name)
 prefix=json.loads((ROOT/'validation/md-game-sprite-frame-world-prefix.json').read_bytes());assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 for name in ['gaw-megadrive.bin','megadrive/out/release/rom.bin']:assert sha((ROOT/name).read_bytes())==old['playable_sha256']
 assert len(list((ROOT/'versions').glob('*/*.bin')))==207
 assert sha((ROOT/'input/original.sms').read_bytes())=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
 assert sha((ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll').read_bytes())=='6c1b76eaec069abf1dca3b82affb1a9116605567847b9bfcd4bf4bb8b572c830'
 out=ROOT/'analysis/md-game-sprite-frame-v0203';m=freeze(ROOT,out,paths,dict(previous_manifest_sha256=sha(previous.read_bytes()),playable_sha256=old['playable_sha256'],reports=reports,native_irq_sat_hidden_dma_verified=True,source_status_supplied=True,patterns_supplied=True,production_integration=False,physical_frame_psg_delivery=False,video_frame_deadlines_accepted=False),[folder],'--cleanup' in sys.argv)
 for item in m['compressed'].values():
  encoded=(out/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes']
 print('Independent physical game sprite archive readback passed.')
if __name__=='__main__':main()
