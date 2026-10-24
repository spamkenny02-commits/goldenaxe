"""Lossless full readback and protected-ROM checks before video diagnostic cleanup."""
import gzip,json,subprocess
from run_core import ROOT
from archive_lossless_evidence import freeze,sha
def main():
 names=['native_irq_video_report.json','native_irq_video_68k_report.json',
        'native_room_reveal_report.json','native_room_reveal_68k_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for key in ['module_sha256','headers_sha256']:
   for n,h in r.get(key,{}).items():assert sha((ROOT/'megadrive/src'/n).read_bytes())==h
 assert reports[0]['cases']==288 and reports[1]['native_cases']==576
 assert reports[2]['checkpoints']==1056 and reports[3]['native_cases']==48
 for report,count in [(reports[1],48),(reports[3],24)]:
  assert all(r['done'] and r['cases']==count and not r['failures'] for r in report['results'])
 roots=[ROOT/'validation'/n for n in ['native-irq-video','native-room-reveal']]
 for d,r in zip(roots,[reports[1],reports[3]]):assert sha((d/'cases.json').read_bytes())==r['source_cases_sha256']
 for r in reports[1]['results']:assert sha((roots[0]/f"kernel-{r['shard']}/out/release/rom.bin").read_bytes())==r['test_rom_sha256']
 assert sha((roots[1]/'kernel/out/release/rom.bin').read_bytes())==reports[3]['test_rom_sha256']
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected};assert len(protected)==278
 assert before['gaw-megadrive.bin']==reports[2]['playable_sha256']
 prefix=json.loads((ROOT/'analysis/native_irq_video_worklog_prefix.json').read_bytes())
 assert sha((ROOT/'analysis/world_next.md').read_bytes()[:prefix['bytes']])==prefix['sha256']
 paths=[p for d in roots for p in d.rglob('*') if p.is_file()];modules=set(reports[2]['module_sha256'])
 for n in list(modules):
  h=n[:-2]+'.h'
  if (ROOT/'megadrive/src'/h).exists():modules.add(h)
 modules.add('source_room_memory.h');paths += [ROOT/'megadrive/src'/n for n in sorted(modules)]
 paths += [ROOT/'analysis'/n for n in names+['native_irq_video.md','native_irq_video_worklog_prefix.json']]
 paths += [ROOT/'tools'/n for n in ['validate_native_irq_video.py','validate_native_irq_video_68k.py',
            'validate_native_room_reveal.py','validate_native_room_reveal_68k.py','archive_native_irq_video.py']]
 out=ROOT/'analysis/native-irq-video-v0275';manifest=freeze(ROOT,out,paths,
  dict(playable_version=275,protected_sha256=before,purpose='Full IRQ video mirrors and continuous native loader binding; outside playable main'),roots,cleanup=True)
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
 for p in [roots[0]/'fixture.sms',roots[0]/'cases.json',roots[1]/'cases.json']:
  assert any(p.resolve().is_relative_to(d.resolve()) for d in roots)
  name=p.relative_to(ROOT).as_posix();assert name not in tracked;e=manifest['compressed'][name];raw=p.read_bytes();encoded=(out/e['stored']).read_bytes()
  assert sha(encoded)==e['stored_sha256'] and sha(raw)==e['raw_sha256'] and gzip.decompress(encoded)==raw
  p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(e['bytes'] for e in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=275,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))
if __name__=='__main__':main()
