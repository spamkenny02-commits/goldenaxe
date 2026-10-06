#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms').read_bytes()
handlers=[rom[0x2B63+2*i]|rom[0x2B64+2*i]<<8 for i in range(128)]
off=12*0x4000+(0xA34E-0x8000); used=set(rom[off:off+4096]);used.discard(0)
native=set(range(1,128))
print(f'handler table: {len(handlers)} entries, {len(set(handlers[1:]))} unique active targets')
print(f'native types: {len(native)}/127')
print(f'legacy types: {127-len(native)}/127')
print(f'map-spawn types: {len(used)}; native map-spawn types: {len(used&native)}; remaining: {len(used-native)}')
print('remaining map types:', ' '.join(map(str,sorted(used-native))))
assert len(handlers)==128 and max(used)==124
