"""Retain display-off wait regression evidence before production changes."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/reveal-wait-v0179';items=[]
 paths=[ROOT/'validation/reveal_wait_report.json',ROOT/'validation/reveal-wait.log',ROOT/'validation/build-reveal-wait.log',ROOT/'tools/reveal_wait_harness.c',ROOT/'tools/build_reveal_wait_harness.ps1',ROOT/'tools/validate_reveal_wait.py',ROOT/'tools/archive_reveal_wait_baseline.py',ROOT/'megadrive/src/main.c',ROOT/'versions/v0179-d018ed93/standard_door_transitions_report.json']
 paths+=sorted((ROOT/'validation/reveal-wait').glob('*/*.bin'))
 for p in paths:
  name=str(p.relative_to(ROOT));data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=name.replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 harness=ROOT.parents[1]/'work/reveal-wait-harness/out/release/rom.bin'
 target=folder/'harness.bin';data=harness.read_bytes()
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 items.append(dict(path='harness.bin',sha256=hashlib.sha256(data).hexdigest()))
 target=folder/'manifest.json';data=(json.dumps(dict(files=items),indent=2)+'\n').encode()
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 print('Display-off wait baseline preserved:',len(items),'files')

if __name__=='__main__':main()
