#!/usr/bin/env python3
from pathlib import Path
import re
bad=[]
for root in ('src','md/src'):
  for p in Path(root).glob('*.c'):
    s=p.read_text()
    for n,line in enumerate(s.splitlines(),1):
      if re.search(r'\(\s*(?:volatile\s+)?uint(?:16|32)_t\s*\*\s*\)',line):
        # MMIO is intentionally word/long sized on Mega Drive.
        if p.name=='platform_md.c' and '0xC0000' in line: continue
        bad.append(f'{p}:{n}: {line.strip()}')
if bad:
  raise SystemExit('unsafe multi-byte casts:\n'+'\n'.join(bad))
assert 'U16_HI_PTR' in Path('src/sms_compat.c').read_text()
print('68000 portability audit: OK')
