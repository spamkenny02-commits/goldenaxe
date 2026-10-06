#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1];asm=(root/'disasm/bank_02_reachable.asm').read_text().splitlines()
world=set(int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]{4})',(root/'src/world_callbacks_512.inc').read_text()))
idx={}
for i,l in enumerate(asm):
 m=re.search(r'B02:\$([0-9A-Fa-f]{4})',l)
 if m: idx.setdefault(int(m.group(1),16),i)
out=[]
for t in sorted(world):
 i=idx.get(t)
 if i is None:continue
 bc=e=None;calls=[];bad=False;ended=False
 for l in asm[i:i+30]:
  m=re.match(r'B02:\$([0-9A-Fa-f]{4})\s+(?:[0-9a-f]{2}\s+)+\s*(.*)',l,re.I)
  if not m:continue
  a=int(m.group(1),16);op=m.group(2).strip()
  if a!=t and a in world:break
  q=re.match(r'LD BC,\$([0-9A-Fa-f]{4})',op)
  if q:bc=int(q.group(1),16)
  q=re.match(r'LD E,\$([0-9A-Fa-f]{2})',op)
  if q:e=int(q.group(1),16)
  q=re.match(r'CALL \$([0-9A-Fa-f]{4})',op)
  if q:calls.append(int(q.group(1),16))
  if op.startswith('JP '):bad=True;break
  if op.startswith('RET'):ended=True;break
 if ended and not bad and calls==[0x6560] and bc is not None and e is not None:out.append((t,bc,e))
(root/'src/world_key_room_callbacks.inc').write_text(''.join(f'{{0x{t:04X}u,0x{p:04X}u,0x{k:02X}u}},\n' for t,p,k in out))
print('key-room callbacks:',len(out))
