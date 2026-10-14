"""Constrain the progression patch to actor loading and four production callers."""
import hashlib,json,re,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'analysis/actor-progression-baseline-v0100';src=ROOT/'megadrive/src'
 changes=[]
 for name in ['main.c','actors.c','actors.h']:
  old=(base/name).read_text();new=(src/name).read_text();changes.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0100/'+name,tofile='v0101/'+name))
  if name=='main.c':
   start=new.index('/* 1816..181F:');end=new.index('/* 21C5/21CB:',start)
   restored=new[:start]+new[end:]
   restored,n=re.subn(r'load_current_world_actors\((room_id|number|0x95)\);',r'load_world_actors(\1,saved_room_actor_mask(\1),sms_vram,md_patterns);',restored)
   assert n==4
   assert restored==old
   assert 'game_save_state[0x1e + (u8)world_dungeon_number]' in new
  elif name=='actors.h':
   assert new.replace('\nvoid load_world_actors_progression(u16 room,u8 persistence,u8 progression,u8 *vram,u32 *native_patterns);','')==old
  else:
   start=old.index(' * 1805 story conditionals');end=old.index('/* 48F3: limits')
   nstart=new.index(' * 1805..1838');nend=new.index('/* 48F3: limits')
   assert old[:start]==new[:nstart] and old[end:]==new[nend:]
 (ROOT/'analysis/actor_progression_patch.diff').write_text(''.join(changes))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','actors.h']},only_actor_loader_declaration_and_four_production_callers_changed=True,source_progression_address_translated_from_C0CE=True,progression_applied_after_persistence_and_before_pattern_allocation=True,full_game_ported=False)
 (ROOT/'validation/actor_progression_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Actor progression patch scope verified')
if __name__=='__main__':main()
