#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1]); b=bytearray(p.read_bytes())
if len(b)<0x200:b.extend(b'\0'*(0x200-len(b)))
if len(b)&1:b.append(0)
def put(o,n,s): b[o:o+n]=s.encode('ascii')[:n].ljust(n,b' ')
put(0x100,16,'SEGA MEGA DRIVE ');put(0x110,16,'(C)OPENAI 2026');put(0x120,48,'GOLDEN AXE WARRIOR C DECOMP');put(0x150,48,'GOLDEN AXE WARRIOR C DECOMP');put(0x180,14,'GM 00000000-00');b[0x18E:0x190]=b'\0\0';put(0x190,16,'J               ')
# ROM start/end, RAM start/end
b[0x1A0:0x1A4]=(0).to_bytes(4,'big');b[0x1A4:0x1A8]=(len(b)-1).to_bytes(4,'big');b[0x1A8:0x1AC]=(0x00FF0000).to_bytes(4,'big');b[0x1AC:0x1B0]=(0x00FFFFFF).to_bytes(4,'big')
# SRAM declaration RA, odd-byte 32 KiB window at 0x200001..0x20FFFF
b[0x1B0:0x1B2]=b'RA';b[0x1B2:0x1B4]=b'\xF8\x20';b[0x1B4:0x1B8]=(0x00200001).to_bytes(4,'big');b[0x1B8:0x1BC]=(0x0020FFFF).to_bytes(4,'big');put(0x1F0,16,'JUE             ')
cs=sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&0xFFFF;b[0x18E:0x190]=cs.to_bytes(2,'big');p.write_bytes(b)
print(f'{p}: {len(b)} bytes checksum {cs:04X}')
