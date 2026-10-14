"""Restricted4A/4B source change and literal-table/ROM integrity audit."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0126-c5e5c136';old=(base/'actors.c').read_text();new=(ROOT/'megadrive/src/actors.c').read_text();s=new
 a=s.index('extern const u8 dungeon_split_data[];');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 dispatch='            else if(entity[0]==0x4a || entity[0]==0x4b) dungeon_split_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);\n';assert s.count(dispatch)==1;s=s.replace(dispatch,'')
 a=s.index('    /* 0940 scans after all behaviors.');b=s.index('\n}\n\n/* 393A',a);s=s[:a]+s[b+1:]
 assert s==old,'Unrelated actor code changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes();asset=ROOT/'megadrive/src/dungeon_split_data.c';literal=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',asset.read_text()));assert literal==source[0x9afd:0x9b1e]
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes();checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_4A_4B_behavior_dispatch_and_post_loop_collision_publication=True,main_source_unchanged_since_v0126=True,literal_table_bytes_exact=33,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',asset,ROOT/'tools/validate_dungeon_split.py',ROOT/'tools/validate_dungeon_split_gameplay.py',ROOT/'tools/validate_dungeon_split_entry.py']},full_game_ported=False,limits=['Controlled state/pending-damage injection and initial native clock alignment; natural weapon strikes, full fights and original clock/RNG remain unproved.','Actual125 first4A appearance excludes random X/Y/direction and other actor records; graphics for all three room types are compared.'])
 (ROOT/'validation/dungeon_split_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only4A/4B behavior/dispatch/post-loop publication added;33 literal bytes and ROM integrity verified.')
if __name__=='__main__':main()
