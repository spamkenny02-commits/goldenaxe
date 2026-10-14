"""Archive v0177 source and source/native gift persistence evidence immutably."""
import hashlib,json
from actor_reference import ROOT

def main():
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 entry=next(e for e in json.loads((ROOT/'versions/index.json').read_text()) if e['sha256']==digest)
 assert entry['version']==177 and entry['validation']=='targeted_checks_passed'
 folder=(ROOT/'versions'/entry['rom']).parent;items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable snapshot differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 for path in sorted((ROOT/'megadrive/src').iterdir()):
  if path.is_file():preserve(path,'source/'+path.name)
 for name in ['main.c','actors.c','house_quest.inc']:preserve(ROOT/'megadrive/src'/name,name)
 preserve(ROOT/'megadrive/out/release/symbol.txt','symbol.txt')
 for name in ['validate_house_quest_gameplay.py','validate_house_quest.py','house_quest_harness.c',
              'build_house_quest_harness.ps1','validate_paid_passage_gameplay.py',
              'audit_quest_gift_persistence_patch.py','archive_quest_gift_persistence_milestone.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for path in sorted((ROOT/'analysis/quest-gift-persistence-v0176').glob('*.json')):
  preserve(path,'reference/'+path.name)
 for name in ['build-v0177.log','build-house-quest-harness-v0177.log',
              'house-quest-persistence-baseline-v0176.log','house-quest-repeat-baseline-v0176.log',
              'house-quest-persistence-v0177.log','house-quest-persistence-high-v0177.log',
              'house-quest-unit-v0177.log','house-quest-hint-v0177.log','paid-passage-gameplay-v0177.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 # Reproduction snapshots for the missing flag and repeated primary3 defect.
 for town in ['27','6a']:
  for region in ['auto','pal']:
   for tag in ['sms','md']:
    capture=ROOT/f'validation/house-quest-persistence-{town}-{region}-{tag}'
    for frame in [3500,4250,4800]:
     for prefix,suffix in [('frame','png'),('ram','bin'),('vram','bin')]:
      path=capture/f'{prefix}_{frame:05d}.{suffix}'
      preserve(path,'captures/'+capture.name+'/'+path.name)
 preserve(ROOT/'analysis/quest_gift_persistence_milestone.md','quest_gift_persistence_milestone.md')
 for report in entry['reports']:preserve(folder/report['file'],report['file'])
 data=(json.dumps(dict(md_sha256=digest,version=177,files=items),indent=2)+'\n').encode()
 target=folder/'source_evidence_manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('v0177 sources and evidence preserved:',len(items),'files')

if __name__=='__main__':main()
