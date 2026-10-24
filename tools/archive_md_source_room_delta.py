"""Full readback of incremental renderer and producer evidence before cleanup."""
import gzip,json,subprocess
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
 names=['md_source_room_delta_report.json','native_irq_video_dirty_report.json',
 'native_irq_video_dirty_68k_report.json','native_contours_dirty_unit_report.json',
 'native_room_contours_dirty_report.json','native_room_contours_dirty_68k_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for key in ['module_sha256','headers_sha256']:
   for n,h in r.get(key,{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['cases']==130 and reports[0]['native_images']==260
 assert reports[1]['cases']==288 and reports[2]['native_cases']==576 and reports[3]['cases']==64
 assert reports[4]['checkpoints']==2592 and reports[5]['native_cases']==48
 roots=[ROOT/'validation'/n for n in ['md-source-room-delta','native-irq-video-dirty','native-contours-dirty-unit','native-room-contours-dirty']]
 assert sha((roots[0]/'out/release/rom.bin').read_bytes())==reports[0]['test_rom_sha256']
 for v in reports[0]['results']:
  assert not v['differences'] and sha((roots[0]/v['region']/f"frame_{v['frame']:05d}.png").read_bytes())==v['image_sha256']
  if v['name'].startswith('noop'):assert not(v['uploaded_patterns'] or v['uploaded_words'] or v['uploaded_clones'])
 for folder,r in [(roots[1],reports[2]),(roots[3],reports[5])]:assert sha((folder/'cases.json').read_bytes())==r['source_cases_sha256']
 for v in reports[2]['results']:
  assert v['done'] and v['cases']==48 and not v['failures']
  assert sha((roots[1]/f"kernel-{v['shard']}/out/release/rom.bin").read_bytes())==v['test_rom_sha256']
 assert all(v['done'] and v['cases']==24 and not v['failures'] for v in reports[5]['results'])
 assert sha((roots[3]/'kernel/out/release/rom.bin').read_bytes())==reports[5]['test_rom_sha256']
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert len(protected)==278
 prefix=json.loads((ROOT/'analysis/md_source_room_delta_worklog_prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()];modules={'source_vdp_dirty.h','source_room_memory.h','pattern_pair_lut.inc'}
 for r in reports:modules.update(r.get('module_sha256',{}));modules.update(r.get('headers_sha256',{}))
 for n in list(modules):
  if n.endswith('.c') and (ROOT/'megadrive/src'/(n[:-2]+'.h')).exists():modules.add(n[:-2]+'.h')
 paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['md_source_room_delta.md','md_source_room_delta_preview.gif','md_source_room_delta_worklog_prefix.json','md_sprite8_palette_report.json']]
 paths += [ROOT/'tools'/n for n in ['validate_md_source_room_delta.py','validate_native_irq_video_dirty.py','validate_native_irq_video_dirty_68k.py','validate_native_contours_dirty_unit.py','validate_native_room_contours_dirty.py','validate_native_room_contours_dirty_68k.py','archive_md_source_room_delta.py']]
 source=ROOT/'validation/sms-vertical-check';paths.append(source/'capture.json')
 for f in [*range(3044,3072),*range(3101,3161)]:paths += [source/f'{kind}_{f:05d}.bin' for kind in ['vram','cram','vdp_regs']]
 out=ROOT/'analysis/md-source-room-delta-v0275';manifest=freeze(ROOT,out,paths,
  dict(playable_version=275,protected_sha256=before,purpose='Incremental SGDK renderer and accumulated IRQ/contour changes; outside playable main'),roots,cleanup=True)
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 generated=[roots[0]/'src/cases.h',roots[1]/'fixture.sms',roots[1]/'cases.json',roots[2]/'fixture.sms',roots[3]/'cases.json']
 for p in generated:
  assert any(p.resolve().is_relative_to(d.resolve()) for d in roots)
  name=p.relative_to(ROOT).as_posix();assert name not in tracked;e=manifest['compressed'][name];raw=p.read_bytes();encoded=(out/e['stored']).read_bytes()
  assert sha(encoded)==e['stored_sha256'] and sha(raw)==e['raw_sha256'] and gzip.decompress(encoded)==raw
  p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(e['bytes'] for e in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=275,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
