#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); b=p.read_bytes()
assert len(b)>=0x200 and len(b)%2==0
assert b[0x100:0x110]==b'SEGA MEGA DRIVE '
assert int.from_bytes(b[0:4],'big')==0x00FFFF00
reset=int.from_bytes(b[4:8],'big'); assert 0x200<=reset<len(b), hex(reset)
assert b[0x1B0:0x1B2]==b'RA'
assert int.from_bytes(b[0x1B4:0x1B8],'big')==0x00200001
assert int.from_bytes(b[0x1B8:0x1BC],'big')==0x0020FFFF
cs=sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&0xffff
assert int.from_bytes(b[0x18E:0x190],'big')==cs
rom_end=int.from_bytes(b[0x1A4:0x1A8],'big'); assert rom_end==len(b)-1
print(f'MD ROM checks: OK ({len(b)} bytes, reset=${reset:06X}, checksum=${cs:04X})')
