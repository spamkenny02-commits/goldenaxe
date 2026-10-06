#!/usr/bin/env python3
from pathlib import Path
import sys
rom=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else Path('/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms').read_bytes()
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).resolve().parents[1]/'src'
out.mkdir(parents=True,exist_ok=True)
def emit(name, data):
    (out/name).write_text(', '.join(f'0x{x:02X}' for x in data)+'\n')
emit('entity32_spawn_types.inc',rom[0x85D6:0x85D9])
emit('entity32_motion.inc',rom[0x85D9:0x85EA])
emit('entity32_spawn_tiles.inc',rom[0x586D:0x5871])
print('phase10 tables generated')
