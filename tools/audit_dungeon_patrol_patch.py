"""Verify the deterministic61/62 translation and its current ROM evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0147-aef23965'
 s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 5065 ->A6C7:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 line='            else if(entity[0]==0x61 || entity[0]==0x62) dungeon_patrol_behavior(entity,tilemap,room,slot);\n'
 assert s.count(line)==1;s=s.replace(line,'')
 s=s.replace('((entity[0]>=0x4a && entity[0]<=0x5e) || entity[0]==0x61 || entity[0]==0x62)','(entity[0]>=0x4a && entity[0]<=0x5e)').replace('(entity[0]<0x56 || entity[0]>0x5e) && entity[0]!=0x61 && entity[0]!=0x62','entity[0]<0x56 || entity[0]>0x5e')
 assert s==(base/'actors.c').read_text(),'Unrelated actor behavior changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes()
 actor=(ROOT/'megadrive/src/actors.c').read_text();v=re.search(r'static const u8 velocity\[\]=\{([^}]+)\};',actor[actor.index('void dungeon_patrol_behavior'):]).group(1)
 assert bytes(int(x.strip(),0) for x in v.split(','))==source[0xa744:0xa754]
 rom=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
 assert rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 names=['dungeon_patrol_allocation_unit_report.json','dungeon_patrol_gameplay_report.json','dungeon_patrol_61_room_entry_report.json','dungeon_patrol_62_room_entry_report.json','dungeon_floor_trap_room_entry_report.json','start_menu_audio_report.json']
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 unit=json.loads((ROOT/'validation'/names[0]).read_text());assert unit['cases']==2463 and unit['all_768_actor_bytes_exact']
 game=json.loads((ROOT/'validation'/names[1]).read_text());assert len(game['cases'])==32 and sum(c['frames'] for c in game['cases'])==2656
 for name in names[2:5]:
  room=json.loads((ROOT/'validation'/name).read_text());assert len(room['cases'])==2
  assert all(c['relative_all_768_actor_bytes_exact']==300 and c['actual_full_room_projectile_and_hero_sat_frames_exact']==300 and not c['excluded_actor_offsets'] for c in room['cases'])
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(rom),checksum=checksum,aliases_and_header_verified=True,main_unchanged_since_v0147=True,prior_actor_implementations_unchanged_since_v0147=True,production_changes_confined_to_61_62_and_publication=True,patrol_velocities_exact_source_A744=True,evidence_sha256=evidence,full_game_ported=False,limits=['Unit routines have no random reads. Production controlled segments align initial world clocks.','Actual127/132 patrol rooms use controlled departure and normal right scroll; all768 actor bytes and hero/projectile SAT compare300 frames after initialization in both regions, without post-load injection. Relative alignment does not establish absolute load timing or original global clock.','Full framebuffer, natural complete travel/combat/progression, remaining quests/audio/ending and hardware remain incomplete or unverified.'])
 (ROOT/'validation/dungeon_patrol_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('61/62-only production changes, exact velocity table, ROM integrity and six current reports verified.')
if __name__=='__main__':main()
