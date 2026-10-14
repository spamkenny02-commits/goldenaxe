"""Immutable production source and selected raw door/music evidence for v0179."""
import hashlib,json
from actor_reference import ROOT

def main():
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==179 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable evidence differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for p in sorted((ROOT/'megadrive/src').iterdir()):
  if p.is_file():preserve(p,'source/'+p.name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['profile_standard_door_music.py','validate_standard_door_transitions.py','audit_standard_door_patch.py','archive_standard_door_milestone.py','validate_dungeon_doors.py','validate_house_quest_gameplay.py','validate_paid_passage_gameplay.py','validate_paid_exit_music.py','profile_paid_passage_loader_phases.py','validate_save.py','validate_paid_passage_native_loading_clock.py','paid_passage_clock_harness.c','build_paid_passage_clock_harness.ps1']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for p in sorted((ROOT/'validation/standard-door-music').rglob('*')):
  if p.is_file():preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation/paid-exit-music').glob('*/*.json')):preserve(p,str(p.relative_to(ROOT)))
 for p in sorted((ROOT/'validation').glob('*v0179.log')):preserve(p,'logs/'+p.name)
 preserve(ROOT/'analysis/standard_door_milestone.md','standard_door_milestone.md')
 preserve(ROOT/'analysis/standard_door_music_report.json','standard_door_music_diagnostic.json')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 data=(json.dumps(dict(version=179,md_sha256=digest,files=items),indent=2)+'\n').encode()
 target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 for item in items:assert hashlib.sha256((folder/item['path']).read_bytes()).hexdigest()==item['sha256']
 print('v0179 source and selected evidence preserved and verified:',len(items),'files')

if __name__=='__main__':main()
