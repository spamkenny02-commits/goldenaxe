"""Archive verified physical-frame diagnostics without touching playable ROMs."""
import json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
 folder=ROOT/'validation/md-source-room-frame';report=json.loads((ROOT/'analysis/md_source_room_frame_report.json').read_bytes())
 assert report['passed'] and report['cases']==39 and report['native_images']==78
 for key in ['module_sha256','headers_sha256']:
  for n,h in report[key].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert sha((folder/'out/release/rom.bin').read_bytes())==report['test_rom_sha256']
 assert sha((ROOT/'analysis/md_sprite8_palette_report.json').read_bytes())==report['calibration_sha256']
 for v in report['results']:
  assert not v['differences'] and sha((folder/v['region']/f"frame_{v['frame']:05d}.png").read_bytes())==v['image_sha256']
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert len(protected)==278
 prefix=json.loads((ROOT/'analysis/md_source_room_frame_worklog_prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 paths=[p for p in folder.rglob('*') if p.is_file()]
 paths += [ROOT/'megadrive/src'/n for n in ['md_source_room_frame.c','md_source_room_frame.h','pattern_convert.c','pattern_convert.h','pattern_pair_lut.inc','source_sms_sprite8.c','source_sms_sprite8.h']]
 paths += [ROOT/'analysis'/n for n in ['md_source_room_frame_report.json','md_source_room_frame.md','md_source_room_frame_preview.png','md_source_room_frame_worklog_prefix.json','md_sprite8_palette_report.json']]
 paths += [ROOT/'tools'/n for n in ['validate_md_source_room_frame.py','archive_md_source_room_frame.py','validate_sms_sprite8.py']]
 source=ROOT/'validation/sms-vertical-check';paths.append(source/'capture.json')
 for f in [3101,3120,3160]:paths += [source/f'{kind}_{f:05d}.bin' for kind in ['vram','cram','vdp_regs']]
 out=ROOT/'analysis/md-source-room-frame-v0275';manifest=freeze(ROOT,out,paths,
  dict(playable_version=275,protected_sha256=before,purpose='Physical static SGDK renderer,78 RGB frame comparisons; outside playable main'),[folder],cleanup=True)
 # Generated input array is already fully read back, like all other payloads.
 generated=folder/'src/cases.h';name=generated.relative_to(ROOT).as_posix();e=manifest['compressed'][name]
 import gzip
 encoded=(out/e['stored']).read_bytes();raw=generated.read_bytes();assert generated.resolve().is_relative_to(folder.resolve())
 assert sha(encoded)==e['stored_sha256'] and sha(raw)==e['raw_sha256'] and gzip.decompress(encoded)==raw
 generated.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(e['bytes'] for e in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=275,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
