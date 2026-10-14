"""Retain missing standard door phases/audio before changing v0178."""
import hashlib,json
from actor_reference import ROOT

def main():
 folder=ROOT/'analysis/standard-door-baseline-v0178';folder.mkdir(exist_ok=True);items=[]
 paths=[ROOT/'analysis/standard_door_music_report.json',ROOT/'tools/profile_standard_door_music.py',ROOT/'tools/archive_standard_door_baseline.py',ROOT/'validation/standard-door-music-v0178.log']
 paths+=sorted((ROOT/'validation/standard-door-music').glob('*/*.json'))
 report=json.loads((ROOT/'analysis/standard_door_music_report.json').read_text())
 for case in report['cases']:
  assert sum(e['command']==0xb0 for e in case['music_sequences']['sms'])==2
  assert not any(e['command']==0xb0 for e in case['music_sequences']['md'])
  p=json.loads((ROOT/f"validation/standard-door-music/{case['name']}-{case['region']}/profiles.json").read_text())
  assert not any(r['resume_phase'] in [1,2,3,4] for r in p['md'].values())
 for path in paths:
  name=path.relative_to(ROOT);target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);data=path.read_bytes()
  if target.exists():assert target.read_bytes()==data
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 prior=ROOT/'versions/v0178-a8d8ee11';rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert rom==(prior/'gaw-megadrive-v0178.bin').read_bytes()
 for path in (ROOT/'megadrive/src').iterdir():
  if path.is_file():assert path.read_bytes()==(prior/'source'/path.name).read_bytes()
 data=(json.dumps(dict(md_sha256=report['md_sha256'],source_sha256=report['source_sha256'],missing_native_fade_and_reveal_stages=True,missing_two_B0_per_roundtrip=True,files=items),indent=2)+'\n').encode();target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('v0178 missing standard door fade/reveal/B0 baseline preserved.')

if __name__=='__main__':main()
