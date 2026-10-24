"""Lossless archive and full readback before native ready-chain diagnostic cleanup."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
 names=['native_hero_initialize_report.json','native_room_tail_report.json','native_room_ready_report.json','native_room_ready_68k_report.json','native_room_ready_performance_report.json','native_actor_assets_report.json','native_actor_remap_report.json','native_room_graphics_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for n,h in r.get('module_sha256',{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
  for n,h in r.get('headers_sha256',{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['cases']==13150 and reports[1]['cases']==288 and reports[2]['checkpoints']==888 and reports[3]['native_cases']==48
 assert all(r['done'] and r['cases']==24 and not r['failures'] for r in reports[3]['results'])
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert before['gaw-megadrive.bin']==reports[2]['playable_sha256']
 roots=[ROOT/'validation'/n for n in ['native-hero-initialize','native-room-tail','native-room-ready','native-room-ready-baseline','native-actor-assets','native-actor-remap','native-room-graphics']]
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()]
 fixture=ROOT/'validation/hero-initialization-cost/source.sms';paths.append(fixture);roots.append(fixture.parent)
 modules=set(reports[2]['module_sha256'])
 for n in list(modules):
  h=n[:-2]+'.h'
  if (ROOT/'megadrive/src'/h).exists():modules.add(h)
 modules.update(['source_room_memory.h','source_irq_context.h'])
 paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['native_room_ready.md','native_room_ready_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_hero_initialize.py','validate_native_room_ready.py','validate_native_room_ready_68k.py','validate_native_room_tail.py','compare_native_room_ready.py','validate_hero_initialization_cost.py','validate_native_room_load.py','archive_native_room_ready.py']]
 out=ROOT/'analysis/native-room-ready-v0275';manifest=freeze(ROOT,out,paths,dict(playable_version=275,protected_sha256=before,purpose='Continuous16D0->1FA7 native hero/scripts/music plus stable remap-row batching; not playable main'),roots,cleanup=True)
 generated=[fixture,*[p for d in roots[:-1] for p in d.glob('fixture.sms')]]
 for p in generated:
  assert any(p.resolve().is_relative_to(d.resolve()) for d in roots);name=p.relative_to(ROOT).as_posix();e=manifest['compressed'][name];raw=p.read_bytes();assert sha(raw)==e['raw_sha256'] and gzip.decompress((out/e['stored']).read_bytes())==raw
  p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for e in manifest['compressed'].values():
  raw=(out/e['stored']).read_bytes();assert sha(raw)==e['stored_sha256'] and sha(gzip.decompress(raw))==e['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(p['bytes'] for p in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=len(protected)-3,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
