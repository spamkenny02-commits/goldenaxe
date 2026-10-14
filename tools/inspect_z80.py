"""Inspect a specified known Z80 code interval; does not classify surrounding bytes."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'work/z80dis'))
from z80dis import z80
p=argparse.ArgumentParser(); p.add_argument('bank',type=lambda x:int(x,0)); p.add_argument('start',type=lambda x:int(x,0)); p.add_argument('end',type=lambda x:int(x,0)); a=p.parse_args()
rom=(ROOT/'input/original.sms').read_bytes(); pc=a.start
while pc<a.end:
    offset=pc if pc<0x8000 else a.bank*0x4000+(pc&0x3fff)
    decoded=z80.decode(rom[offset:offset+8],pc)
    print(f'ROM {offset:05X} CPU {pc:04X} {rom[offset:offset+decoded.len].hex():12} {z80.disasm(decoded)}')
    pc+=decoded.len or 1
