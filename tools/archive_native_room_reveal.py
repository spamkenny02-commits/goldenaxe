"""Freeze/read back native reveal/fade evidence before generated-file cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 names=['native_room_reveal_report.json','native_room_reveal_68k_report.json',
        'native_room_fade_report.json','native_room_fade_68k_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for key in ['module_sha256','headers_sha256']:
   for n,h in r.get(key,{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['cases']==24 and reports[0]['checkpoints']==1056
 assert reports[1]['native_cases']==48 and reports[2]['cases']==96 and reports[3]['native_cases']==192
 for r,expected in [(reports[1],24),(reports[3],96)]:
  assert all(v['done'] and v['cases']==expected and not v['failures'] for v in r['results'])
 roots=[ROOT/'validation'/n for n in ['native-room-reveal','native-room-fade']]
 for folder,r in zip(roots,[reports[1],reports[3]]):
  assert sha((folder/'cases.json').read_bytes())==r['source_cases_sha256']
  assert sha((folder/'kernel/out/release/rom.bin').read_bytes())==r['test_rom_sha256']
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected}
 assert len(protected)==278 and before['gaw-megadrive.bin']==reports[0]['playable_sha256']
 prefix=json.loads((ROOT/'analysis/native_room_reveal_worklog_prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()]
 modules=set(reports[0]['module_sha256'])
 for n in list(modules):
  h=n[:-2]+'.h'
  if (ROOT/'megadrive/src'/h).exists():modules.add(h)
 modules.add('source_room_memory.h')
 paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['native_room_reveal.md','native_room_reveal_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_room_reveal.py','validate_native_room_reveal_68k.py',
            'validate_native_room_fade.py','validate_native_room_fade_68k.py','archive_native_room_reveal.py']]
 out=ROOT/'analysis/native-room-reveal-v0275'
 manifest=freeze(ROOT,out,paths,dict(playable_version=275,protected_sha256=before,
  purpose='Continuous native loading/reveal/fade through first contour wait; not playable main'),roots,cleanup=True)
 fixture=roots[1]/'fixture.sms';name=fixture.relative_to(ROOT).as_posix();e=manifest['compressed'][name]
 assert fixture.resolve().is_relative_to(roots[1].resolve())
 encoded=(out/e['stored']).read_bytes();raw=fixture.read_bytes()
 assert sha(encoded)==e['stored_sha256'] and sha(raw)==e['raw_sha256'] and gzip.decompress(encoded)==raw
 fixture.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(e['bytes'] for e in manifest['removed_verified_generated'])
 stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=len(protected)-3,
            removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
