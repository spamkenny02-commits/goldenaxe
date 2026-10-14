"""Restrict4F..51 AI plus projectile18 and verify literal resources/ROM integrity."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0131-a41f0e2f';old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 4FD2 ->9DA6:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 dispatch='            else if(entity[0]>=0x4f && entity[0]<=0x51) dungeon_hunter_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);\n';assert s.count(dispatch)==1;s=s.replace(dispatch,'')
 s=s.replace('(entity[0]>=0x4a && entity[0]<=0x51)','(entity[0]>=0x4a && entity[0]<=0x4e)').replace('(entity[0]>=0x10 && entity[0]<=0x18)','(entity[0]>=0x10 && entity[0]<=0x17)').replace(' || entity[0]==0x18 ||',' ||').replace('type==0x18?dungeon_hunter_shot:','')
 assert s==old,'Unrelated actor code changed';assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();asset=ROOT/'megadrive/src/dungeon_hunter_data.c';literal=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',asset.read_text()));assert literal==source[0x4036:0x404c]
 for filename,name,start,size in [('first_boss_data.c','first_boss_movement',0x87cd,17),('actor_data.c','actor_charge_sequence',0x927f,17)]:
  p=ROOT/'megadrive/src'/filename;data=re.search(name+r'\[\]\s*=\s*\{(.*?)\}',p.read_text(),re.S).group(1);assert bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',data))==source[start:start+size]
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes();checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_4F_50_51_helpers_dispatch_publication_and_projectile18=True,prior_actor_and_main_implementations_unchanged_since_v0131=True,new_literal_bytes_exact=22,reused_walk_and_charge_bytes_exact=34,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',asset,ROOT/'tools/validate_dungeon_hunter.py',ROOT/'tools/validate_dungeon_hunter_gameplay.py']},full_game_ported=False,limits=['Controlled actor/hero states and native initial clock alignment. Full charge uses zero collision-map injection.','Shot allocation/chance/pursuit decisions are direct-routine checks; production tests inject projectile18 and compare flight through removal.','Actual room appearance checks exclude random X/Y/direction. Whole RNG/global clock and full natural combat remain unproved.'])
 (ROOT/'validation/dungeon_hunter_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only4F/50/51 and projectile18 added;56 literal bytes and ROM integrity verified.')
if __name__=='__main__':main()
