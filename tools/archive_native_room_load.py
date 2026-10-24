"""Lossless freeze of continuous native loader evidence; preserve playable ROMs."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 names=['native_room_load_report.json','native_room_load_actors_report.json','native_room_load_68k_report.json','native_room_load_actors_68k_report.json','native_actor_list_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for n,h in r.get('module_sha256',{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
  for n,h in r.get('helpers',{}).items():assert sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes())==h
  for n,h in r.get('headers_sha256',{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['cases']==reports[1]['cases']==24 and reports[1]['checkpoints']==528 and reports[-1]['cases']==9216
 for r in reports[2:4]:assert len(r['results'])==2 and all(p['done'] and p['cases']==24 and not p['failures'] for p in r['results'])
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert before['gaw-megadrive.bin']==reports[0]['playable_sha256']
 roots=[ROOT/'validation'/n for n in ['native-room-load','native-room-load-actors','native-actor-list']]
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()]
 modules=list(reports[0]['module_sha256'])+list(reports[0]['headers_sha256'])
 paths += [ROOT/'megadrive/src'/n for n in modules]
 paths += [ROOT/'analysis'/n for n in names+['native_room_load.md','native_room_load_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_room_load.py','validate_native_room_load_68k.py','validate_native_actor_list.py','archive_native_room_load.py']]
 out=ROOT/'analysis/native-room-load-v0275'
 manifest=freeze(ROOT,out,paths,dict(playable_version=275,protected_sha256=before,purpose='Continuous native16D0->1853 with active source audio IRQs; not integrated into playable main'),roots,cleanup=True)
 fixture=ROOT/'validation/native-actor-list/fixture.sms';name=fixture.relative_to(ROOT).as_posix();entry=manifest['compressed'][name];raw=fixture.read_bytes()
 assert fixture.resolve().is_relative_to(roots[-1].resolve()) and sha(raw)==entry['raw_sha256'] and gzip.decompress((out/entry['stored']).read_bytes())==raw
 fixture.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for e in manifest['compressed'].values():
  raw=(out/e['stored']).read_bytes();assert sha(raw)==e['stored_sha256'] and sha(gzip.decompress(raw))==e['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(p['bytes'] for p in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=len(protected)-3,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))

if __name__=='__main__':main()
