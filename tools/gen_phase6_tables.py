#!/usr/bin/env python3
from pathlib import Path
import sys
rom=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms').read_bytes()
out=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/gaw_decomp_phase6/src')
out.mkdir(parents=True,exist_ok=True)

def bytes_inc(name,base,count):
    vals=rom[base:base+count]
    (out/name).write_text('\n'.join('    '+','.join(f'0x{x:02X}' for x in vals[i:i+16])+(',' if i+16<count else '') for i in range(0,count,16))+'\n')
def words_inc(name,base,count):
    vals=[rom[base+2*i]|rom[base+2*i+1]<<8 for i in range(count)]
    (out/name).write_text('\n'.join('    '+','.join(f'0x{x:04X}' for x in vals[i:i+8])+(',' if i+8<count else '') for i in range(0,count,8))+'\n')
bytes_inc('player_motion_normal.inc',0x33DB,6*17)
bytes_inc('player_motion_alt.inc',0x3441,6*17)
words_inc('player_sprite_normal.inc',0x3B67,256)
words_inc('player_sprite_mode3.inc',0x3D67,8)
words_inc('player_sprite_death.inc',0x3D77,2)
words_inc('player_sprite_state11.inc',0x3D7B,8)
bytes_inc('player_action_anim.inc',0x3635,44)
words_inc('player_action_targets.inc',0x2EDB,12)
words_inc('player_state_targets.inc',0x2EF3,13)
bytes_inc('player_stat_lookup.inc',0x2D9E,48)
# Bank 12, CPU $A269. RST $0008 indexes this byte-wise.
bank12_a269=12*0x4000+(0xA269-0x8000)
bytes_inc('player_contact_thresholds.inc',bank12_a269,64)
print('phase6 tables generated')
