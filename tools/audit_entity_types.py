#!/usr/bin/env python3
from pathlib import Path
import re,sys,json,subprocess,hashlib
from embed_rom import REFERENCE_SHA256
root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit('Usage: python3 tools/audit_entity_types.py /path/to/reference.sms')
rom=Path(sys.argv[1]).read_bytes()
if len(rom)!=0x40000 or hashlib.sha256(rom).hexdigest()!=REFERENCE_SHA256:
    raise SystemExit('Unsupported reference ROM')
handlers=[rom[0x2B63+2*i]|rom[0x2B64+2*i]<<8 for i in range(128)]
checked_in=[int(v,16) for v in re.findall(r'0x([0-9A-Fa-f]{4})',(root/'src/entity_handlers.inc').read_text())]
assert handlers==checked_in, 'checked-in entity handler table differs from reference ROM'
off=12*0x4000+(0xA34E-0x8000); used=set(rom[off:off+4096]);used.discard(0)
probe=root/'runtime_coverage_host_test'
if not probe.exists(): raise SystemExit('Build actual-dispatcher probe with make runtime_coverage_host_test')
native=set(json.loads(subprocess.check_output([str(probe)],text=True))['native_entity_types'])
print(f'handler table: {len(handlers)} entries, {len(set(handlers[1:]))} unique active targets')
print(f'native types: {len(native)}/127')
print(f'legacy types: {127-len(native)}/127')
print(f'map-spawn types: {len(used)}; native map-spawn types: {len(used&native)}; remaining: {len(used-native)}')
print('remaining map types:', ' '.join(map(str,sorted(used-native))))
assert len(handlers)==128 and max(used)==124
