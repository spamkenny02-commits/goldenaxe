"""Freeze contour/chain/scalar evidence, read back fully, then remove generated files."""
import gzip,json,subprocess
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
 names=['native_room_contours_report.json','native_room_contours_68k_report.json',
        'native_contours_unit_report.json','native_room_contours_performance_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for key in ['module_sha256','headers_sha256']:
   for n,h in r.get(key,{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['checkpoints']==2592 and reports[1]['native_cases']==48 and reports[2]['cases']==64
 assert all(r['done'] and r['cases']==24 and not r['failures'] for r in reports[1]['results'])
 roots=[ROOT/'validation'/n for n in ['native-room-contours','native-contours-unit','native-room-contours-baseline']]
 assert sha((roots[0]/'cases.json').read_bytes())==reports[1]['source_cases_sha256']
 assert sha((roots[0]/'kernel/out/release/rom.bin').read_bytes())==reports[1]['test_rom_sha256']
 old=json.loads((roots[2]/'report.json').read_bytes())
 assert old['source_cases_sha256']==reports[1]['source_cases_sha256']==sha((roots[2]/'cases.json').read_bytes())
 assert sha((roots[2]/'rom.bin').read_bytes())==old['test_rom_sha256']
 assert sha((roots[2]/'source_room_contours.c').read_bytes())==reports[3]['baseline_module_sha256']
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert len(protected)==278
 assert before['gaw-megadrive.bin']==reports[0]['playable_sha256']
 prefix=json.loads((ROOT/'analysis/native_room_contours_worklog_prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()];modules=set(reports[0]['module_sha256'])
 for n in list(modules):
  h=n[:-2]+'.h'
  if (ROOT/'megadrive/src'/h).exists():modules.add(h)
 modules.add('source_room_memory.h');paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['native_room_contours.md','native_room_contours_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_room_contours.py','validate_native_room_contours_68k.py',
            'validate_native_contours_unit.py','compare_native_room_contours.py','archive_native_room_contours.py']]
 out=ROOT/'analysis/native-room-contours-v0275';manifest=freeze(ROOT,out,paths,
  dict(playable_version=275,protected_sha256=before,purpose='Continuous native16D0..2002 including16 contours and stable word batching; outside playable main'),roots,cleanup=True)
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 for p in [roots[1]/'fixture.sms',roots[0]/'cases.json',roots[2]/'cases.json']:
  assert any(p.resolve().is_relative_to(d.resolve()) for d in roots)
  name=p.relative_to(ROOT).as_posix();assert name not in tracked;e=manifest['compressed'][name];raw=p.read_bytes();encoded=(out/e['stored']).read_bytes()
  assert sha(encoded)==e['stored_sha256'] and sha(raw)==e['raw_sha256'] and gzip.decompress(encoded)==raw
  p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(e['bytes'] for e in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=275,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
