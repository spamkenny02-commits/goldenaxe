"""Freeze source/native history diagnostics before deleting generated binaries."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 names=['history_timed_source_report.json','history_prefix_timed_source_report.json','history_timed_68k_report.json']
 reports=[json.loads((ROOT/'analysis'/n).read_bytes()) for n in names]
 for r in reports:
  assert r['passed']
  for name,h in r['module_sha256'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==h
 assert reports[-1]['native_cases']==18432
 protected=[ROOT/'input/original.sms',ROOT/'gaw-megadrive.bin',ROOT/'gaw-title-megadrive.bin',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected}
 assert before['gaw-megadrive.bin']==reports[-1]['playable_rom_sha256']
 folders=[ROOT/'validation'/n for n in ['history-timed','history-prefix-timed','history-timed-68k']]
 paths=[p for d in folders for p in d.rglob('*') if p.is_file()]
 paths += [ROOT/'analysis'/n for n in names+['history_timed_native.md','history_timed_worklog_prefix.json']]
 paths += [ROOT/'megadrive/src'/n for n in reports[0]['module_sha256']]
 paths += [ROOT/'tools'/n for n in ['validate_history_timed.py','validate_history_timed_68k.py','archive_history_timed.py']]
 out=ROOT/'analysis/history-timed-native-v0275'
 manifest=freeze(ROOT,out,paths,dict(playable_version=275,protected_sha256=before,purpose='Native clocked room-history and enemy-loader prefix; diagnostic only'),folders,cleanup=True)
 for folder in folders[:2]:
  for p in folder.glob('fixture-*.sms'):
   assert p.resolve().is_relative_to(folder.resolve())
   name=p.relative_to(ROOT).as_posix();entry=manifest['compressed'][name];raw=p.read_bytes()
   assert sha(raw)==entry['raw_sha256'] and gzip.decompress((out/entry['stored']).read_bytes())==raw
   p.unlink();manifest['removed_verified_generated'].append(dict(path=name,bytes=len(raw)))
 (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
 for entry in manifest['compressed'].values():
  raw=(out/entry['stored']).read_bytes();assert sha(raw)==entry['stored_sha256'];assert sha(gzip.decompress(raw))==entry['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 removed=sum(p['bytes'] for p in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(dict(full_readback=True,numbered_roms_preserved=len(protected)-3,removed_bytes=removed,archive_bytes=stored,net_freed_bytes=removed-stored))

if __name__=='__main__':main()
