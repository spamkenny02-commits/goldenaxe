#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
rom_path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms')
rom=rom_path.read_bytes()
if len(rom)<0x40000: raise SystemExit('expected 256 KiB SMS ROM')
def rb(bank,addr,n):
    o=(bank&15)*0x4000+(addr&0x3fff); return rom[o:o+n]
def emit_bytes(path,data,cols=16):
    lines=[]
    for i in range(0,len(data),cols): lines.append(', '.join(f'0x{x:02X}' for x in data[i:i+cols])+',')
    (root/'src'/path).write_text('\n'.join(lines)+'\n')
# Bank 12: 512 world cells x 8 local entity types.
emit_bytes('world_entity_types.inc',rb(12,0xA34E,512*8))
# Bank 12: type >= 32 configuration [HP, attack, defense, flags].
emit_bytes('map_entity_stats.inc',rb(12,0xA0EA,96*4))
# Bank 2: resource descriptor [bank/transform, source lo, source hi].
res=rb(2,0x825F,96*3); emit_bytes('map_entity_resources.inc',res)
# Precompute the number of 8x8 tiles occupied by each map-loadable resource.
# $032A writes four planes; for valid map resources each plane expands to the
# same byte count. $1780 advances C by expanded_plane_bytes / 8.
spans=[]
for t in range(32,128):
    i=(t-32)*3; a=res[i]; bank=a&15; src=res[i+1]|(res[i+2]<<8); lens=[]
    for plane in range(4):
        out=0
        for _ in range(0x10000):
            cmd=rb(bank,src,1)[0]; src=(src+1)&0xffff
            if cmd==0: break
            n=cmd&0x7f; out+=n
            src=(src+(n if cmd&0x80 else 1))&0xffff
        else: raise SystemExit(f'bad compressed resource type {t}')
        lens.append(out)
    # Aux-only records may not be resources; only require exactness for types
    # that appear in the 512x8 map spawn table.
    used=t in set(rb(12,0xA34E,512*8))
    if used and (len(set(lens))!=1 or lens[0]%8):
        raise SystemExit(f'invalid map resource type {t}: {lens}')
    spans.append((lens[-1]//8)&0xff if len(set(lens))==1 and lens[-1]%8==0 else 0)
emit_bytes('map_entity_resource_spans.inc',bytes(spans))
print('generated gameplay-init tables')
