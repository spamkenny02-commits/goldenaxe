#!/usr/bin/env python3
from pathlib import Path
import sys
rom_path=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms')
out=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/gaw_decomp_phase9/src')
rom=rom_path.read_bytes(); out.mkdir(parents=True,exist_ok=True)
if len(rom)!=0x40000: raise SystemExit('expected 256 KiB ROM')
def emit(name,b,per=16):
    lines=[]
    for i in range(0,len(b),per):
        lines.append('    '+','.join(f'0x{x:02X}' for x in b[i:i+per])+(',' if i+per<len(b) else ''))
    (out/name).write_text('\n'.join(lines)+'\n')
def fixed(a,n): return rom[a:a+n]
def phys(bank,cpu): return bank*0x4000+(cpu-0x8000)
# Type 1 death/drop tables in bank 12: 32 saved-type ids, parallel drop classes,
# and the compact probability/spawn-type lookup beginning at $A2AE.
emit('death_saved_types.inc', rom[phys(12,0xA26E):phys(12,0xA26E)+32])
emit('death_drop_classes.inc', rom[phys(12,0xA28E):phys(12,0xA28E)+32])
emit('death_drop_rules.inc', rom[phys(12,0xA2AE):phys(12,0xA2AE)+32])
# Arthur action entities (types 3 and 5).
emit('action_type3_sprite.inc', rom[phys(2,0x8411):phys(2,0x8411)+16])
emit('action_type3_velocity.inc', fixed(0x39BC,8))
emit('action_type3_offset.inc', fixed(0x39C4,8))
emit('action_type4_velocity.inc', fixed(0x3A92,8))
emit('action_type4_offsets_a.inc', fixed(0x3AF7,8))
emit('action_type4_offsets_b.inc', fixed(0x3AFF,8))
emit('action_type4_tiles_interior.inc', fixed(0x3AD9,8))
emit('action_type4_tiles_world.inc', fixed(0x3AE2,20))
emit('action_type4_tiles_alt.inc', fixed(0x3AEE,8))
emit('action_type5_velocity.inc', fixed(0x3A1F,8))
emit('action_type5_attack.inc', fixed(0x2D9E,32))
# Type 28 header + 8-way motion table, type 29 2-way ballistic launch table,
# and type 31 header + 8-way motion table.
emit('entity28_config.inc', fixed(0x415C,38))
emit('entity29_launch.inc', fixed(0x4277,10))
emit('entity31_config.inc', fixed(0x4366,38))
print('phase9 tables generated from',rom_path)
