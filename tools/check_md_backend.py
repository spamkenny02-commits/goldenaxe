#!/usr/bin/env python3
from pathlib import Path
import re, tempfile, subprocess
p=Path('md/src/platform_md.c').read_text()
assert 'vdp_reg(16,0x00)' in p, 'Plane A must be 32 cells wide for 32-column shadow upload'
assert '0x40000000u' in p and '0xC0000000u' in p, '32-bit VDP VRAM/CRAM command codes missing'
assert 'VDP_CTRL32' in p, 'VDP address commands must use the 32-bit control port'
# Validate command formula independently.
def cmd(a,code): return code | ((a & 0x3fff)<<16) | ((a>>14)&3)
assert cmd(0x0000,0x40000000)==0x40000000
assert cmd(0xC000,0x40000000)==0x40000003
assert cmd(0xD800,0x40000000)==0x58000003
assert cmd(0x0000,0xC0000000)==0xC0000000
# Header/checksum script smoke test on a synthetic ROM.
with tempfile.TemporaryDirectory() as d:
    f=Path(d)/'r.bin'; f.write_bytes(bytes(range(256))*4)
    subprocess.run(['python3','md/fix_header.py',str(f)],check=True,stdout=subprocess.DEVNULL)
    b=f.read_bytes(); assert b[0x100:0x110]==b'SEGA MEGA DRIVE '
    assert b[0x1B0:0x1B2]==b'RA'
    expected=sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&0xffff
    assert int.from_bytes(b[0x18e:0x190],'big')==expected
print('MD backend static checks: OK')
