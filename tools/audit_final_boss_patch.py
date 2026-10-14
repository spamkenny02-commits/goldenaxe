"""Verify55F1/63 behavior scope and the hero equipment accessor."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'megadrive/src';baseline=ROOT/'analysis/final-boss-baseline-v0116';old=(baseline/'actors.c').read_text();new=(src/'actors.c').read_text();s=new
 a=s.index('/* 55F1/560A:');b=s.index('/* 45C4:',a);s=s[:a]+s[b:]
 s=s.replace('            else if(entity[0]==0x6d) final_boss_behavior(entity,hero_x,hero_y,NULL,world_final_boss_weapon_valid());\n','')
 old_condition=next(l for l in old.splitlines() if 'if((entity[0]==0x0f' in l);new_condition=next(l for l in s.splitlines() if 'if((entity[0]==0x0f' in l)
 s=s.replace(new_condition,old_condition)
 s=s.replace('if(e[0]==0x64 && (choice&15)<13)','if((choice&15)<13)')
 s=s.replace('else if(entity[0]==0x63 || entity[0]==0x64)','else if(entity[0]==0x64)')
 s=s.replace('if(entity[0]==0x64 && (gate&15)<4) choice=random();','if((gate&15)<4) choice=random();')
 assert s==old,'Unrelated actor implementation changed'
 main_old=(baseline/'main.c').read_text();main_new=(src/'main.c').read_text()
 accessor='/* 55F8: selected item1 at level2 is required for type6D pending damage. */\nbool world_final_boss_weapon_valid(void) { return hero_selected_item==1 && hero_weapon_level==2; }\n'
 assert main_new.replace(accessor,'')==main_old,'Unrelated main code changed'
 previous=json.loads((ROOT/'versions/v0116-e7069055/sword_boss_patch_audit.json').read_text())
 assert sha(src/'sword_boss_data.c')==previous['source_files']['sword_boss_data.c']
 (ROOT/'analysis/final_boss_patch.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='v0116/actors.c',tofile='v0118/actors.c'))+''.join(difflib.unified_diff(main_old.splitlines(True),main_new.splitlines(True),fromfile='v0116/main.c',tofile='v0118/main.c')))
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),source_files={n:sha(src/n) for n in ['main.c','actors.c','sword_boss_data.c']},only_type6D_behavior_type63_shared_behavior_dispatch_collision_publication_and_equipment_accessor_changed=True,shared_projectiles_renderer_and_literal_tables_unchanged=True,original_random_stream_reproduced=False,full_game_ported=False)
 (ROOT/'validation/final_boss_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Types6D/63 scope verified; other AI, projectiles, renderer and assets unchanged')
if __name__=='__main__':main()
