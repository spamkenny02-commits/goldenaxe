#!/usr/bin/env python3
from pathlib import Path
import csv,sys
rom_path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms')
out_root=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/gaw_decomp_phase2')
rom=rom_path.read_bytes(); out=out_root/'analysis'/'dispatch_tables.csv'; out.parent.mkdir(parents=True,exist_ok=True)
def byte(bank,a):
    if a<0x400: return rom[a]
    if a<0x4000: return rom[bank*0x4000+a]
    if a<0x8000: return rom[0x4000+(a-0x4000)]
    return rom[bank*0x4000+(a-0x8000)]
def word(bank,a): return byte(bank,a)|(byte(bank,a+1)<<8)
rows=[]
def add(name,bank,base,indices,note=''):
 for i in indices: rows.append([name,f'{bank:02X}',f'{base:04X}',i,f'{word(bank,base+2*i):04X}',note])
add('main_state',0,0x00DC,range(12),'index = RAM_MAIN_STATE / 2')
add('frame_quadrant',0,0x1EAD,range(4),'index = frame_counter & 3')
add('entity_type',0,0x2B63,range(1,33),'type 0 skipped; 32 nonzero entity types')
add('entity_hit_variant',0,0x2830,range(4),'4-way dispatch used by damage/hit path')
add('effect_state',1,0x6AF1,range(1,5),'state 0 skipped')
add('state_73DD',1,0x73DD,range(4),'four handlers observed')
add('world_cell_callback',2,0xB762,range(0xC0),'C0B9 range 00..BF; callback bank forced to 2')
add('audio_E0_FF',6,0x86F3,[i for i in range(32) if i!=15],'E0..FF command table; index 15 points to data $897F and is excluded')
with out.open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['table','bank','base_cpu','index','target_cpu','note']); w.writerows(rows)
print(out)
