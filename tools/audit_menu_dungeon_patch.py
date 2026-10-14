"""Scope and ROM integrity audit for menu fixes and four pending dungeon helpers."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';old=(ROOT/'analysis/dungeon-phase-baseline-v0118/actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('static u8 dungeon_phase_roll(');b=s.index('/* 5071 -> A86D:',a);s=s[:a]+s[b:]
 s=s.replace('            else if(entity[0]==0x46) dungeon_proximity_behavior(entity,tilemap,hero_x,hero_y,room,slot,NULL);\n','').replace('            else if(entity[0]>=0x47 && entity[0]<=0x49) dungeon_phase_behavior(entity,cells,hero_x,hero_y,frame,slot,NULL);\n','').replace(' || (entity[0]>=0x46 && entity[0]<=0x49)','')
 assert s==old,'Unrelated actor changes'
 baseline=(ROOT/'analysis/final-boss-baseline-v0116/main.c').read_text();current=(src/'main.c').read_text();s=current
 accessor='/* 55F8: selected item1 at level2 is required for type6D pending damage. */\nbool world_final_boss_weapon_valid(void) { return hero_selected_item==1 && hero_weapon_level==2; }\n';assert s.count(accessor)==1;s=s.replace(accessor,'')
 a=s.index('/* 20DA clears only');b=s.index('static void enter_initial_room',a)
 oa=baseline.index('/* 70F2..7218/72C4:');ob=baseline.index('static void enter_initial_room',oa)
 s=s[:a]+baseline[oa:ob]+s[b:]
 hook='sound_stop();sound_music(0x89); /* 14F3..14F5: New Game / Continue theme. */';assert s.count(hook)==1;s=s.replace(hook,'sound_stop();')
 assert s==baseline,'Unrelated main changes'
 data=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535;assert int.from_bytes(data[0x18e:0x190],'big')==checksum
 assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff') and data[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),rom_bytes=len(data),checksum=checksum,aliases_and_header_verified=True,actor_changes_confined_to_46_49_helpers_dispatch_and_collision_publication=True,main_changes_confined_to_inventory_and_start_menu_music_since_v0118=True,source_files={str(p.relative_to(ROOT)):sha(p) for p in [src/'main.c',src/'actors.c',ROOT/'tools/validate_menu_transitions.py',ROOT/'tools/validate_start_menu_audio.py',ROOT/'tools/validate_dungeon_phase.py']},full_game_ported=False,limits=['46..49 have864 isolated cases; their natural room/gameplay paths remain unverified.','Menu timing model retains an approximate reconstruction reserve; six natural routes provide targeted evidence only.'])
 (ROOT/'validation/menu_dungeon_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 (ROOT/'analysis/menu_dungeon_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0118/actors.c',tofile='v0125/actors.c'))+''.join(difflib.unified_diff(baseline.splitlines(True),current.splitlines(True),fromfile='v0116/main.c',tofile='v0125/main.c')))
 print('ROM aliases/checksum/header and restricted menu/46..49 source changes verified.')
if __name__=='__main__':main()
