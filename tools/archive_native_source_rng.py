"""Freeze native RNG source, host/68000 checks and isolated cartridge evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/native-source-rng-v0183';items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as output:output.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name not in ['source_rng.c','source_rng.h']:assert p.read_bytes()==(ROOT/'analysis/audio-noise-note-v0183/source-v0183'/p.name).read_bytes()
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest();assert digest=='ec1677f7fd5b45ff86a6a910488b47302ef759e5bfadd26332a1f3ded3bef876'
 for p in ['megadrive/src/source_rng.c','megadrive/src/source_rng.h','tools/validate_native_source_rng.py','tools/validate_native_source_rng_68k.py','tools/archive_native_source_rng.py','tools/source_rng_reference.py','tools/source_rng_refresh.py','tools/run_core.py','analysis/native_source_rng_report.json','analysis/native_source_rng_68k_report.json','analysis/native_source_rng_milestone.md','validation/native-source-rng.log','validation/native-source-rng-68k.log']:
  preserve(ROOT/p,p)
 for p in sorted((ROOT/'validation/native-source-rng').iterdir()):
  if p.is_file():preserve(p,str(p.relative_to(ROOT)))
 base=ROOT/'validation/native-rng-68k'
 for p in sorted((base/'src').iterdir()):preserve(p,str(p.relative_to(ROOT)))
 for name in ['build.log','out/release/rom.bin','out/release/symbol.txt','auto/capture.json','pal/capture.json']:preserve(base/name,'validation/native-rng-68k/'+name)
 host=json.loads((ROOT/'analysis/native_source_rng_report.json').read_text());cpu=json.loads((ROOT/'analysis/native_source_rng_68k_report.json').read_text())
 assert (host['seed_cases'],host['output_cases'],host['refresh_cases'])==(65536,196608,66816)
 assert cpu['executed_68000'] and len(cpu['rows'])==2 and all(r['failures']==0 for r in cpu['rows'])
 data=(json.dumps(dict(production_md_sha256=digest,files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as output:output.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('Native RNG source and execution evidence archived:',len(items),'files')
if __name__=='__main__':main()
