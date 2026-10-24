"""Freeze graphics/loading source/native evidence before generated-file cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 names=['native_actor_graphics_report.json','native_actor_remap_report.json','native_actor_assets_report.json','native_room_graphics_report.json','native_room_graphics_68k_report.json','native_room_load_actors_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for n,h in r['module_sha256'].items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
  for n,h in r.get('headers_sha256',{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[2]['loaded_types']==80 and reports[2]['cases']==156 and reports[1]['cases']==96
 assert reports[3]['checkpoints']==624 and reports[4]['native_cases']==48 and all(r['done'] and r['cases']==24 and not r['failures'] for r in reports[4]['results'])
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert before['gaw-megadrive.bin']==reports[3]['playable_sha256']
 roots=[ROOT/'validation'/n for n in ['native-actor-graphics','native-actor-remap','native-actor-assets','native-room-graphics']]
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()]
 modules=set(reports[3]['module_sha256'])
 for n in list(modules):
  h=n[:-2]+'.h'
  if (ROOT/'megadrive/src'/h).exists():modules.add(h)
 paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['native_room_graphics.md','native_room_graphics_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_actor_graphics.py','validate_native_actor_remap.py','validate_native_actor_assets.py','validate_native_room_graphics.py','validate_native_room_graphics_68k.py','validate_native_room_load.py','archive_native_room_graphics.py']]
 out=ROOT/'analysis/native-room-graphics-v0275';manifest=freeze(ROOT,out,paths,dict(playable_version=275,protected_sha256=before,purpose='Continuous native16D0->18E1 plus every room-list graphic type; not playable main'),roots,cleanup=True)
 for root in roots:
  for p in root.glob('fixture.sms'):
   assert p.resolve().is_relative_to(root.resolve());name=p.relative_to(ROOT).as_posix();e=manifest['compressed'][name];raw=p.read_bytes();assert sha(raw)==e['raw_sha256'] and gzip.decompress((out/e['stored']).read_bytes())==raw
   p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for e in manifest['compressed'].values():
  raw=(out/e['stored']).read_bytes();assert sha(raw)==e['stored_sha256'] and sha(gzip.decompress(raw))==e['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(p['bytes'] for p in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=len(protected)-3,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))

if __name__=='__main__':main()
