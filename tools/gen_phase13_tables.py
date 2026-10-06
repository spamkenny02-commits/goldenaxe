#!/usr/bin/env python3
from pathlib import Path
import sys
rom=Path(sys.argv[1]).read_bytes(); out=Path(sys.argv[2]);out.mkdir(exist_ok=True)
def emit(n,d):(out/n).write_text(', '.join(f'0x{x:02X}' for x in d)+'\n')
emit('sine_table.inc',rom[0x8000:0x8100])
emit('entity35_target_offsets.inc',rom[0x8750:0x8756])
emit('entity38_variant.inc',rom[0x87C4:0x87C7])
emit('entity38_motion_fast.inc',rom[0x87CD:0x87DE])
