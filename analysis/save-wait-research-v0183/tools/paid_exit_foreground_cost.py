"""Combine instruction-derived paid-exit work,keeping waits and IRQs explicit."""
from class0_graphics_loading_cost import class0_graphics_cost
from world_map_loading_cost import world_map_cost
from map_hud_loading_cost import map_hud_cost
from full_actor_loading_cost import full_actor_cost
from room_history_loading_cost import clear_and_history_cost
from hero_initialization_cost import hero_initialization_cost
from world_load_tail_cost import room_script_setup_cost,world_music_setup_cost,load_return_cost
from reveal_loading_cost import reveal_prefix_cost,reveal_prepare_cost_excluding_save_spin

def paid_exit_foreground_cost(rom,hero_entry_ram,history_attempts):
 r=hero_entry_ram;room=int.from_bytes(r[0xb9:0xbb],'little')
 assert len(r)==8192 and r[0x40]==0 and r[0xac]==0 and r[0x41]!=5 and r[0xf1]<=3
 gems=sum((1<<n) if r[0xcf+n]&128 else 0 for n in range(9))
 HUD=map_hud_cost(rom,r[0x318],r[0xda],r[0xdb],r[0xdc],r[0xdd],gems,r[0x2f],r[0xbf])
 parts=dict(graphics=class0_graphics_cost(rom)['foreground_tstates'],
            map_caller=17+world_map_cost(rom,room,r[0x100+room])['foreground_tstates'],
            HUD_caller_excluding_save_spin=17+HUD['foreground_excluding_wait_save_spin'],
            call24C5=17,
            clear_and_history=clear_and_history_cost(history_attempts)['foreground_tstates'],
            actors=full_actor_cost(rom,room,r[0x200+room])['foreground_tstates'],
            actor_return_and_hero_call=10+17,
            hero=hero_initialization_cost(rom,r)['foreground_tstates'],
            script_caller=17+room_script_setup_cost(r[0xa2]),
            music_caller=17+world_music_setup_cost(rom,room,0xb0)['foreground_tstates'],
            load_return=load_return_cost())
 to_reveal=sum(parts.values())
 parts['VRAM_clear']=reveal_prefix_cost()['foreground_tstates']
 parts['reveal_prepare_excluding_save_spin']=reveal_prepare_cost_excluding_save_spin()
 return dict(to1FA7_excluding_HUD_save_spin=to_reveal,to0ACE_excluding_two_save_spins=sum(parts.values()),components=parts,scope='Changed class1->class0 six paid exits,C0AC0,old terrain!=5,valid armor0..3,ordinary non-boss actors. Hero-entry state/history branch inputs supplied. No wait-length,IRQ-cost or physical frame prediction.')
