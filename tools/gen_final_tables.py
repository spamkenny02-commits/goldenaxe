#!/usr/bin/env python3
from pathlib import Path
import sys
rom=Path(sys.argv[1]).read_bytes(); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
def emit(name,start,end): (out/name).write_text(', '.join(f'0x{x:02X}' for x in rom[start:end])+'\n')
emit('entity51_probe.inc',0x8F3A,0x8F46)
emit('entity51_ballistic.inc',0x8F46,0x8F56)
emit('entity53_motion.inc',0x85EA,0x85FB)
emit('entity58_charge.inc',0x927F,0x9290)
emit('entity118_path_data.inc',0x4745,0x47F7)
