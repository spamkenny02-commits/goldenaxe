"""Archive new v0177 evidence separately from its immutable original snapshot."""
import hashlib,json
from actor_reference import ROOT

def main():
 prior=ROOT/'versions/v0177-3f4dbbc9';folder=prior/'additional-persistence';folder.mkdir(exist_ok=True)
 items=[]
 def preserve(path,name):
  data=path.read_bytes();target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==data,('immutable follow-up differs',name)
  else:
   with target.open('xb') as handle:handle.write(data)
  items.append(dict(path=str(name).replace('\\','/'),sha256=hashlib.sha256(data).hexdigest()))
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert rom==(prior/'gaw-megadrive-v0177.bin').read_bytes()
 for path in (ROOT/'megadrive/src').iterdir():
  if path.is_file():assert path.read_bytes()==(prior/'source'/path.name).read_bytes()
 for name in ['run_core.py','validate_house_quest_gameplay.py','validate_quest_gift_save.py',
              'validate_save.py','audit_quest_gift_persistence_followup.py',
              'archive_quest_gift_persistence_followup.py']:
  preserve(ROOT/'tools'/name,'tools/'+name)
 for name in ['house_quest_revisit_gameplay_report.json','quest_gift_save_report.json',
              'house_quest_cold_persistence_gameplay_report.json','quest_gift_persistence_followup_report.json']:
  preserve(ROOT/'validation'/name,'reports/'+name)
 for name in ['house-quest-revisit-v0177.log','quest-gift-save-v0177.log','house-quest-cold-v0177.log']:
  preserve(ROOT/'validation'/name,'logs/'+name)
 cases=json.loads((ROOT/'validation/quest_gift_save_report.json').read_text())['cases']
 for case in cases:
  stem=f"{case['town']:02x}-{case['region']}"
  for tag in ['sms','md']:
   path=ROOT/f'validation/quest-gift-save-{stem}-{tag}.srm';preserve(path,'SRAM/'+path.name)
   gift=ROOT/f'validation/house-quest-persistence-{stem}-{tag}/ram_04800.bin'
   preserve(gift,'gift-state/'+gift.parent.name+'/'+gift.name)
   for prefix,frame in [('quest-gift-cold-',1920),('house-quest-revisit-',6500),('house-quest-cold-persistence-',4800)]:
    capture=ROOT/f'validation/{prefix}{stem}-{tag}'
    for kind,extension in [('ram','bin'),('frame','png'),('vram','bin')]:
     path=capture/f'{kind}_{frame:05d}.{extension}'
     preserve(path,'captures/'+capture.name+'/'+path.name)
 preserve(ROOT/'analysis/quest_gift_persistence_followup.md','README.md')
 data=(json.dumps(dict(version=177,md_sha256=hashlib.sha256(rom).hexdigest(),production_ROM_changed=False,files=items),indent=2)+'\n').encode()
 target=folder/'manifest.json'
 if target.exists():assert target.read_bytes()==data
 else:
  with target.open('xb') as handle:handle.write(data)
 print('v0177 additional persistence evidence preserved:',len(items),'files; ROM unchanged.')

if __name__=='__main__':main()
