"""Lossless archive/readback before generated test cleanup; never touches playable ROMs."""
import gzip,json
from run_core import ROOT
from archive_lossless_evidence import freeze,sha

def main():
 roots=[ROOT/'validation'/n for n in ['rng-timed-host','rng-timed-68k','room-history']]
 protected=[ROOT/'input/original.sms',*sorted((ROOT/'versions').glob('*/*.bin'))]
 before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in protected}
 names=['source_rng_timed.c','source_rng_timed.h','source_room_history.c','source_room_history.h','main.c','save.inc']
 paths=[*[p for folder in roots for p in folder.rglob('*') if p.is_file()],*[ROOT/'megadrive/src'/n for n in names],*[ROOT/'analysis'/n for n in ['rng_timed_host_report.json','rng_timed_68k_report.json','room_history_rules_report.json','room_history_v0274_report.json','room_history_v0274.md']]]
 out=ROOT/'analysis/room-history-v0274'
 manifest=freeze(ROOT,out,paths,dict(release=274,purpose='Timed RNG isolated research and integrated room-history evidence',cleanup_roots=[p.relative_to(ROOT).as_posix() for p in roots],protected_sha256=before),roots,cleanup=True)
 saved=json.loads((out/'manifest.json').read_bytes())
 for name,item in saved['compressed'].items():
  raw=(out/item['stored']).read_bytes();assert sha(raw)==item['stored_sha256'];assert sha(gzip.decompress(raw))==item['raw_sha256']
 for p in protected:assert sha(p.read_bytes())==before[p.relative_to(ROOT).as_posix()]
 freed=sum(x['bytes'] for x in manifest['removed_verified_generated']);stored=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
 print(json.dumps(dict(archive=str(out),removed_generated_bytes=freed,archive_bytes=stored,net_freed_bytes=freed-stored,protected_numbered_roms=len(protected)-1,full_readback_passed=True),indent=2))
if __name__=='__main__':main()
