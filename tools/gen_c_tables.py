#!/usr/bin/env python3
from pathlib import Path
import sys

rom_path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms')
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/gaw_decomp_phase3/src')
rom=rom_path.read_bytes()

def word_phys(p): return rom[p] | (rom[p+1]<<8)
def cpu_bank_phys(bank,cpu):
    if cpu < 0x4000: return bank*0x4000 + cpu
    if cpu < 0x8000: return bank*0x4000 + (cpu-0x4000)
    return bank*0x4000 + (cpu-0x8000)
def words_at_phys(p,n): return [word_phys(p+2*i) for i in range(n)]
def emit(name,vals,per=8):
    with (out/name).open('w') as f:
        for i in range(0,len(vals),per):
            tail=',' if i+per < len(vals) else ''
            f.write('    '+','.join(f'0x{x:04X}' for x in vals[i:i+per])+tail+'\n')

emit('main_states.inc', words_at_phys(0x00DC,12),6)
# Table base has an unused word at index 0; type 1 starts at base+2.
ent=words_at_phys(0x2B63,128)
emit('entity_handlers.inc',ent,8)
emit('entity_hit.inc',words_at_phys(0x2830,4),4)
world_p=2*0x4000+(0xB762-0x8000)
emit('world_callbacks_512.inc',words_at_phys(world_p,512),8)
print('generated C tables from',rom_path)
