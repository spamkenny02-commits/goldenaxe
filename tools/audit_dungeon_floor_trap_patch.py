"""Verify the deterministic5E/77 translation and its current ROM evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0146-edc3758a'
 s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 5059 ->A50B:');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 a=s.index('/* 47F7/4804/4821:');b=s.index('extern const u8 burst_boss_shot_template',a);s=s[:a]+s[b:]
 for line in ['            else if(entity[0]==0x5e) dungeon_floor_trap_behavior(entity,room,slot);\n','            else if(entity[0]==0x77) dungeon_floor_shot_behavior(entity);\n']:
  assert s.count(line)==1;s=s.replace(line,'')
 s=s.replace('type==0x77?dungeon_floor_shot:','').replace(' || entity[0]==0x77','').replace('entity[0]<=0x5e','entity[0]<=0x5d').replace('entity[0]>0x5e','entity[0]>0x5d')
 assert s==(base/'actors.c').read_text(),'Unrelated actor behavior changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 source=(ROOT/'input/original.sms').read_bytes()
 template=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',(ROOT/'megadrive/src/dungeon_floor_trap_data.c').read_text()))
 assert template==source[0x4843:0x4859]
 rom=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
 assert rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 names=['dungeon_floor_trap_allocation_unit_report.json','dungeon_floor_trap_gameplay_report.json','dungeon_floor_trap_room_entry_report.json','dungeon_emitter_gameplay_report.json','start_menu_audio_report.json']
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 unit=json.loads((ROOT/'validation'/names[0]).read_text());assert unit['cases']==2029 and unit['all_768_actor_bytes_exact']
 game=json.loads((ROOT/'validation'/names[1]).read_text());assert len(game['cases'])==30 and sum(c['frames'] for c in game['cases'])==1882
 room=json.loads((ROOT/'validation'/names[2]).read_text());assert len(room['cases'])==2
 assert all(c['relative_all_768_actor_bytes_exact']==300 and c['actual_full_room_projectile_and_hero_sat_frames_exact']==300 and not c['excluded_actor_offsets'] for c in room['cases'])
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(rom),checksum=checksum,aliases_and_header_verified=True,main_unchanged_since_v0146=True,prior_actor_implementations_unchanged_since_v0146=True,production_changes_confined_to_5E_77_and_publication=True,projectile_template_exact_source_4843=True,evidence_sha256=evidence,full_game_ported=False,limits=['Unit routines have no random reads. Production controlled segments align initial world clocks.','Actual140 uses controlled departure141 and normal left scroll; all768 actor bytes and hero/projectile SAT compare300 frames after initialization in both regions, without post-load injection. Relative alignment does not establish absolute load timing or original global clock.','Full framebuffer, natural complete travel/combat/progression, remaining quests/audio/ending and hardware remain incomplete or unverified.'])
 (ROOT/'validation/dungeon_floor_trap_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('5E/77-only production changes, exact template, ROM integrity and five current reports verified.')
if __name__=='__main__':main()
