"""Restrict54/55 behavior and71 projectile additions."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0137-775552e0';old=(base/'actors.c').read_text();s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 5008 ->9FFC:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 d='            else if(entity[0]==0x54 || entity[0]==0x55) dungeon_emitter_behavior(entity,room,slot,hero_x,hero_y,NULL);\n';assert s.count(d)==1;s=s.replace(d,'')
 s=s.replace('type==0x71?dungeon_emitter_shot:','').replace('entity[0]==0x70 || entity[0]==0x71 || entity[0]==0x72','entity[0]==0x70 || entity[0]==0x72').replace('entity[0]==0x18 || entity[0]==0x71 || (entity[0]>=0x46','entity[0]==0x18 || (entity[0]>=0x46').replace('(entity[0]>=0x4a && entity[0]<=0x55)','(entity[0]>=0x4a && entity[0]<=0x53)')
 assert s==old,'Unrelated actor implementation changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes(),'Main game changed'
 source=(ROOT/'input/original.sms').read_bytes();asset=ROOT/'megadrive/src/dungeon_emitter_data.c'
 literal=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]{2})',asset.read_text()));assert literal==source[0x43bc:0x43d2]
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,production_changes_confined_to_54_55_AI_71_template_dispatch_and_collision_publication=True,prior_actor_and_main_implementations_unchanged_since_v0137=True,literal_bytes_exact=22,original_random_stream_reproduced=False,source_files={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'megadrive/src/main.c',ROOT/'megadrive/src/actors.c',asset,ROOT/'tools/validate_dungeon_emitter.py',ROOT/'tools/validate_dungeon_emitter_gameplay.py',ROOT/'tools/validate_dungeon_emitter_entry.py']},full_game_ported=False,limits=['Initial production clock explicitly aligned for controlled segments; source random reads controlled only in isolated cases.','Actual143/128 scroll/load compares fixed X/Y/direction; initial appearance records exclude random cooldown byte4 and align to first initialization. Other records and absolute loading cadence not compared.','Full natural fights, RNG/global clock, framebuffer/SAT, complete audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_emitter_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Only54/55 AI and71 template/dispatch/publication added;22 literal bytes and ROM integrity verified.')
if __name__=='__main__':main()
