#!/usr/bin/env python3
from pathlib import Path
import sys
rom_path=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms')
out=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/gaw_decomp_phase8/src')
rom=rom_path.read_bytes(); out.mkdir(parents=True,exist_ok=True)
if len(rom)!=0x40000: raise SystemExit('expected 256 KiB ROM')

def phys(bank,cpu):
    if not 0x8000 <= cpu < 0xC000: raise ValueError(hex(cpu))
    return bank*0x4000+(cpu-0x8000)
def emit_u16(name, vals, per=8):
    lines=[]
    for i in range(0,len(vals),per):
        lines.append('    '+','.join(f'0x{x:04X}' for x in vals[i:i+per])+(',' if i+per<len(vals) else ''))
    (out/name).write_text('\n'.join(lines)+'\n')
def emit_u8(name, vals, per=16):
    lines=[]
    for i in range(0,len(vals),per):
        lines.append('    '+','.join(f'0x{x:02X}' for x in vals[i:i+per])+(',' if i+per<len(vals) else ''))
    (out/name).write_text('\n'.join(lines)+'\n')

# $B762..$BB61: exactly 512 little-endian callback pointers. $BB62 starts
# the overworld event table used by $1976.
p=phys(2,0xB762)
callbacks=[rom[p+2*i] | (rom[p+2*i+1]<<8) for i in range(512)]
emit_u16('world_callbacks_512.inc',callbacks)

# $190B selects banks 8..11 from high(id*2), then reads a pointer from the
# first 256 bytes of that bank. Preserve the four source banks verbatim so
# the C decompressor can execute the original $0C00 format.
for bank in range(8,12):
    emit_u8(f'world_map_bank_{bank:02d}.inc',rom[bank*0x4000:(bank+1)*0x4000])

# Independently validate the $0C00 C=1 stream for all 512 IDs. Every map must
# terminate after exactly 160 output bytes.
def map_output_len(world_id):
    doubled=world_id*2; bank=8+(doubled>>8); po=doubled&0xFF
    base=bank*0x4000
    cpu=rom[base+po] | (rom[base+po+1]<<8)
    if not 0x8000 <= cpu < 0xC000: raise SystemExit(f'bad map ptr id={world_id:03X}')
    p=base+(cpu-0x8000); outn=0
    while True:
        cmd=rom[p]; p+=1
        if cmd==0: return outn
        if cmd&0x80:
            n=cmd&0x7F; p+=n; outn+=n
        else:
            n=cmd; p+=1; outn+=n
        if outn>160: raise SystemExit(f'map overflow id={world_id:03X}: {outn}')
for wid in range(512):
    n=map_output_len(wid)
    if n!=160: raise SystemExit(f'map id={wid:03X} expands to {n}, expected 160')

# Bank-5 $BE78 auxiliary interior records: 38-cell special list and 11 x 16
# byte records beginning at $BEB8.
emit_u8('world_interior_special_cells.inc',rom[phys(5,0xBF68):phys(5,0xBF68)+0x26])
emit_u8('world_interior_aux_records.inc',rom[phys(5,0xBEB8):phys(5,0xBEB8)+11*16])
print('phase8 tables generated from',rom_path)
