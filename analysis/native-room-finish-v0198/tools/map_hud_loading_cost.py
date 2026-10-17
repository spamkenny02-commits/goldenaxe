"""Original1DE2 map/HUD/palette work, separated from0B95 save/spin wait."""
from hud_loading_cost import hud_cost
from room_map_loading_cost import room_map_cost

def palette_restore_cost(clock,curse=0):
 total=sum([10,10,10,16+15*21,13,4,10,11,4,4,12,7,6,7,4,10,16,13,4])
 if not curse:total+=12
 else:
  total+=7+13+4+4
  total+=12 if clock&2 else 7+10+16
 total+=13+7+(12 if clock&2 else 7+4)+13+10
 return total

def map_transfer_cost_excluding_save_spin():
 #229C/0BB3: retain CALL0B95 and its register restore; omit0B95..0BB3.
 restore=sum([10,13,14,14,10,10,10,10,4,4,10,10,10,10,10])
 pre=sum([11,11,11,11,17,4,4,11,7,11,10,10,7])
 #OUTI and DJNZ both decrement B:128 output bytes per outer iteration.
 transfer=12*(128*(16+13)-5+4+10)
 post=sum([11,4,10,10,10,10,10])
 return pre+restore+transfer+post

def wait_save_spin_cost(repeated_loops):
 #0B95..0BB3; interrupted work is excluded,register restore is outside.
 return sum([11,11,11,11,4,4,11,11,11,11,15,15,13,11,7,13,4])+repeated_loops*(13+4+12)+13+4+7

def map_hud_cost(rom,health,health_max,magic,magic_max,gold,gems,clock,curse=0):
 parts=dict(map_preparation=17+room_map_cost()['foreground_tstates'],
            HUD=17+hud_cost(rom,health,health_max,magic,magic_max,gold,gems)['foreground_tstates'],
            map_transfer_excluding_save_spin=17+map_transfer_cost_excluding_save_spin(),
            palette=palette_restore_cost(clock,curse))
 return dict(foreground_excluding_wait_save_spin=sum(parts.values()),components=parts,scope='Original1DE2 including fall-through palette return,ordinary valid armor0..3.0B95..0BB3 save/spin excluded;149-T register restore retained. Clock argument is value after original wait.')
