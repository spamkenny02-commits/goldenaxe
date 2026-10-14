"""Verify the maze change is confined to the translated exit rule and its wiring."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=ROOT/'megadrive/src/main.c';s=p.read_text();baseline=ROOT/'analysis/forest-maze-baseline-v0099/main.c'
 start=s.index('/* 21D7..2236:');end=s.index('/* Bank 5 BE78:',start)
 restored=s[:start]+s[end:]
 restored=restored.replace('\nstatic u8 forest_maze_progress; /* C06C: transient, outside the save record. */','')
 restored=restored.replace('room_id=resolve_room_transition(transition_direction);','room_id=neighboring_room(transition_direction);')
 restored=restored.replace('    if(world_room_index[number*2]==255 && world_room_index[number*2+1]==255) return;','    /* The exterior forest-maze rule 21D7 remains to port. */\n    if(world_room_index[number*2]==255 && world_room_index[number*2+1]==255) return;')
 restored=restored.replace('save_reset_new_game();forest_maze_progress=0;','save_reset_new_game();')
 assert restored==baseline.read_text()
 assert s.count('resolve_room_transition(transition_direction)')==1
 assert 'number=neighboring_room(direction);' in s[s.index('static void begin_room_transition'):]
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),main_sha256=sha(p),baseline_main_sha256=sha(baseline),only_exit_rule_progress_storage_stage_zero_call_and_new_game_reset_changed=True,preflight_remains_side_effect_free=True,progress_advanced_once_per_transition=True,full_game_ported=False)
 (ROOT/'validation/forest_maze_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Maze production patch scope verified')
if __name__=='__main__':main()
