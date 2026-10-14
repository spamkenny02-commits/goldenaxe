"""Preserve v0180 exact source and selected raw transition evidence."""
import hashlib,json
from actor_reference import ROOT

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==180 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(p,name):
  data=p.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as f:f.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in sorted((ROOT/'megadrive/src').iterdir()):
  if p.is_file():preserve(p,'source/'+p.name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['reveal_wait_harness.c','build_reveal_wait_harness.ps1','validate_reveal_wait.py','audit_reveal_wait_patch.py','archive_reveal_wait_milestone.py','profile_standard_door_music.py','validate_standard_door_transitions.py','validate_paid_passage_gameplay.py','validate_save.py','validate_resume.py','validate_resume_capacity.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for p in sorted((ROOT/'validation/standard-door-music').rglob('*')):
  if p.is_file():preserve(p,str(p.relative_to(ROOT)))
 for name in ['sms-resume-detail','md-resume-detail']:
  for p in sorted((ROOT/'validation'/name).iterdir()):
   if p.is_file():preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation').glob('*v0180.log')):preserve(p,'logs/'+p.name)
 preserve(ROOT/'analysis/reveal_wait_milestone.md','reveal_wait_milestone.md')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 baseline=ROOT/'analysis/reveal-wait-v0179/manifest.json'
 data=(json.dumps(dict(version=180,md_sha256=digest,baseline_manifest_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),files=items),indent=2)+'\n').encode();target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as f:f.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('v0180 source and selected evidence archived and verified:',len(items),'files')

if __name__=='__main__':main()
