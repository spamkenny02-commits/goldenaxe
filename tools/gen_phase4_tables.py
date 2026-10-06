#!/usr/bin/env python3
from pathlib import Path
import sys
rom = Path(sys.argv[1]).read_bytes()
out = Path(sys.argv[2])
# $8100-$81BF in bank 2: 48 collision rectangles, 4 bytes each.
boxes = rom[0x8100:0x81C0]
assert len(boxes) == 48*4
with (out/'src'/'hitboxes.inc').open('w') as f:
    for i in range(48):
        b=boxes[i*4:i*4+4]
        f.write('    {' + ','.join(f'0x{x:02X}' for x in b) + '},')
        f.write(f' /* {i:02d} */\n')
# 22-byte spawn/motion configuration blocks used by $3DAF/$3ED6.
configs = {
 16:0x3E53, 17:0x3E76, 18:0x3EB6, 19:0x3F57, 20:0x3F8A, 21:0x3FBD,
 22:0x3FF0, 23:0x4013, 24:0x4036, 25:0x4062, 26:0x409B, 27:0x40CB, 30:0x428E,
}
with (out/'src'/'enemy_configs.inc').open('w') as f:
    for typ,addr in configs.items():
        size = 38 if typ in (19,20,21,30) else 22
        b=rom[addr:addr+size]
        f.write(f'    [{typ}] = {{' + ','.join(f'0x{x:02X}' for x in b) + f'}}, /* ROM ${addr:04X} */\n')

with (out/'src'/'enemy_config25_alt.inc').open('w') as f:
    b=rom[0x4078:0x4078+22]
    f.write(','.join(f'0x{x:02X}' for x in b) + '\n')
