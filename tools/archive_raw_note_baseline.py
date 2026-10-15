"""Retain reproduced v0180 raw-note regression before production correction."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/raw-note-duration-v0180';items=[]
 paths=[ROOT/'analysis/raw_note_duration_baseline_report.json',ROOT/'megadrive/src/sound.inc',ROOT/'tools/validate_raw_note_duration.py',ROOT/'tools/raw_note_duration_harness.c',ROOT/'tools/build_raw_note_duration_harness.ps1',ROOT/'tools/archive_raw_note_baseline.py',ROOT/'validation/raw-duration-baseline.log',ROOT/'validation/build-raw-duration-baseline.log']
 paths+=sorted((ROOT/'validation/raw-note-duration').glob('*.bin'))
 for p in paths:
  name=str(p.relative_to(ROOT));data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=name.replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 p=ROOT.parents[1]/'work/raw-note-duration-harness/out/release/rom.bin';data=p.read_bytes();target=folder/'native-harness.bin'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 items.append(dict(path='native-harness.bin',sha256=hashlib.sha256(data).hexdigest()))
 report=json.loads((ROOT/'analysis/raw_note_duration_baseline_report.json').read_text());assert report['cases']==1080 and all(r['mismatches']==540 for r in report['rows'])
 data=(json.dumps(dict(md_sha256=report['md_sha256'],files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 print('v0180 raw-note baseline preserved:',len(items),'files')

if __name__=='__main__':main()
