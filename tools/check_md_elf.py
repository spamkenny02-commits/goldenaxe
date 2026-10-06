#!/usr/bin/env python3
"""Check the actual linked 68000 address map, not just the cartridge header."""
import argparse
from pathlib import Path
import subprocess

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path)
    parser.add_argument('--nm',default='m68k-elf-nm')
    args=parser.parse_args()
    header=args.elf.read_bytes()[:20]
    if header[:7]!=b'\x7fELF\x01\x02\x01' or header[18:20]!=b'\x00\x04':
        parser.exit(1,'Expected a big-endian ELF32 Motorola 68000 image\n')
    symbols={}
    for line in subprocess.check_output([args.nm,'-n',str(args.elf)],text=True).splitlines():
        fields=line.split()
        if len(fields)==3:
            symbols[fields[2]]=(int(fields[0],16),fields[1])
    required=('_start','__data_load','__data_start','__data_end','__bss_start','__bss_end','gaw_ram','gaw_audio_tick','gaw_irq_service')
    if any(name not in symbols for name in required):
        parser.exit(1,'Missing startup/native runtime symbols\n')
    address=lambda name:symbols[name][0]
    assert address('_start')==0x200
    assert address('__data_load')<0x200000
    assert 0xFF0000<=address('__data_start')<=address('__data_end')<=address('__bss_start')<=address('__bss_end')<=0xFFFF00
    assert address('__bss_start')<=address('gaw_ram')<address('__bss_end')
    for name,(value,kind) in symbols.items():
        if kind in 'BbDd' and not 0xFF0000<=value<=0xFFFF00:
            parser.exit(1,f'Mutable symbol {name} is outside work RAM: {value:08X}\n')
        if name.startswith(('gaw_sms_compat_','gaw_recompiled_')):
            parser.exit(1,f'Instruction interpreter linked into console image: {name}\n')
    print(f'MD ELF checks: OK (native-only; RAM {address("__bss_start"):06X}-{address("__bss_end"):06X})')

if __name__=='__main__':main()
