"""Restricted4C helper/dispatch/publication, literal table and ROM integrity audit."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0129-8960a965';old=(base/'actors.c').read_text();new=(ROOT/'megadrive/src/actors.c').read_text();s=new
 a=s.index('extern const u8 dungeon_hop_data[];');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 dispatch='            else if(entity[0]==0x4c) dungeon_hop_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);\n';assert s.count(dispatch)==1;s=s.replace(dispatch,'')
 condition='(entity[0]>=0x4a && entity[0]<=0x4c)';assert s.count(condition)==1;s=s.replace(condition,'(entity[0]==0x4a || entity[0]==0x4b)')
 assert s==old,'Unrelated actor code changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();asset=ROOT/'megadrive/src/dungeon_hop_data.c';literal=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',asset.read_text()));assert literal==source[0x9b28:0x9b58]
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes();checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_4C_behavior_dispatch_and_collision_publication=True,main_and_prior_actor_source_unchanged_since_v0129=True,literal_table_bytes_exact=48,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',asset,ROOT/'tools/validate_dungeon_hop.py',ROOT/'tools/validate_dungeon_hop_gameplay.py',ROOT/'tools/validate_dungeon_hop_entry.py']},full_game_ported=False,limits=['Controlled state injection and initial native clock alignment. Production flight segments stop before random cooldown; copying/choices are checked only in direct routine cases.','Actual14E first4C appearance excludes random X/Y/direction and other actor records.','Full natural jump/copy cycles and source RNG/global clock remain unproved.'])
 (ROOT/'validation/dungeon_hop_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only4C helper/dispatch/collision publication added;48 literal bytes and ROM integrity verified.')
if __name__=='__main__':main()
