"""Verify the 5F/60 melee translation and its current ROM evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0148-0a3927a9'
 s=(ROOT/'megadrive/src/actors.c').read_text()
 a=s.index('/* 505F ->A566:');b=s.index('/* 5065 ->A6C7:',a);s=s[:a]+s[b:]
 line='            else if(entity[0]==0x5f || entity[0]==0x60) dungeon_melee_behavior(entity,tilemap,cells,hero_x,hero_y,frame,slot,NULL);\n'
 assert s.count(line)==1;s=s.replace(line,'')
 s=s.replace('(entity[0]>=0x4a && entity[0]<=0x62)','((entity[0]>=0x4a && entity[0]<=0x5e) || entity[0]==0x61 || entity[0]==0x62)').replace('entity[0]<0x56 || entity[0]>0x62','(entity[0]<0x56 || entity[0]>0x5e) && entity[0]!=0x61 && entity[0]!=0x62')
 assert s==(base/'actors.c').read_text(),'Unrelated actor behavior changed'
 assert (ROOT/'megadrive/src/main.c').read_bytes()==(base/'main.c').read_bytes()
 rom=(ROOT/'gaw-megadrive.bin').read_bytes()
 assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
 assert rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 names=['dungeon_melee_allocation_unit_report.json','dungeon_melee_gameplay_report.json','dungeon_melee_5f_entry_report.json','dungeon_melee_60_entry_report.json','dungeon_melee_attack_5f_entry_report.json','dungeon_melee_attack_60_auto_diagnostic.json','dungeon_melee_attack_60_pal_diagnostic.json','dungeon_patrol_61_room_entry_report.json','dungeon_patrol_62_room_entry_report.json','start_menu_audio_report.json']
 evidence={}
 for name in names:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 unit=json.loads((ROOT/'validation'/names[0]).read_text());assert unit['cases']==1984 and unit['all_768_actor_bytes_exact']
 game=json.loads((ROOT/'validation'/names[1]).read_text());assert len(game['cases'])==58 and sum(c['frames'] for c in game['cases'])==1278
 for name in names[7:9]:
  room=json.loads((ROOT/'validation'/name).read_text());assert len(room['cases'])==2
  assert all(c['relative_all_768_actor_bytes_exact']==300 and c['actual_full_room_projectile_and_hero_sat_frames_exact']==300 for c in room['cases'])
 attack=json.loads((ROOT/'validation'/names[4]).read_text());assert len(attack['cases'])==2 and all(c['controlled_cycle_actor_hero_gold_sound_frames_exact']==34 and c['controlled_cycle_sat_frames_exact']==33 for c in attack['cases'])
 diagnostic=json.loads((ROOT/'validation'/names[6]).read_text());assert diagnostic['all_768_actor_bytes_and_hero_state_animation_gold_HP_hurt_position_velocity_and_effects_exact_frames']==34 and diagnostic['sat_exact_frames']==32 and len(diagnostic['sat_differences'])==1
 assert diagnostic['sat_differences'][0]['frame']==3702
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(rom),checksum=checksum,aliases_and_header_verified=True,main_unchanged_since_v0148=True,prior_actor_implementations_unchanged_since_v0148=True,production_changes_confined_to_5F_60_and_publication=True,evidence_sha256=evidence,full_game_ported=False,known_actual_attack_sprite_order_discrepancy=dict(type=0x60,region='pal',frame=3702),limits=['Four original random-read sites use controlled input shims in isolated cases; production deterministic segments align initial world clocks. Original random stream is not reproduced.','Actual117/138 appearance aligns to initialization and excludes random X/Y/direction. Controlled actual-room attacks compare all actor/hero/effect fields34 frames in each of four room/region cases.5F PAL/NTSC and60 NTSC SAT33 frames match;60 PAL has one retained sprite order mismatch at3702, strict validator fails. Native renderer always sorts by Y; source0940 may instead rotate through objects based on sourceC047/VDP overflow. Root cause requires further renderer investigation.','Main/older AI unchanged; mismatch is retained, not hidden by timeline shift or assertion relaxation. Full natural progression, global clock/RNG, full framebuffer/audio, quests, ending and hardware remain incomplete or unverified.'])
 (ROOT/'validation/dungeon_melee_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('5F/60-only AI changes and current evidence verified;60 PAL one-frame SAT order gap retained.')
if __name__=='__main__':main()
