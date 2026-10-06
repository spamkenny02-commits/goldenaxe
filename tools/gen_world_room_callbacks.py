#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
asm=(root/'disasm/bank_02_reachable.asm').read_text().splitlines()
world=[int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]{4})',(root/'src/world_callbacks_512.inc').read_text())]
worldset=set(world)
# Collect each callback's straight-line wrapper until RET/JP. We accept only
# wrappers made exclusively from one or more $6594 calls and optional $5FB1.
idx={}
for i,l in enumerate(asm):
 m=re.search(r'B02:\$([0-9A-Fa-f]{4})',l)
 if m: idx.setdefault(int(m.group(1),16),i)
actions=[]; targets=[]; finalize=[]
for t in sorted(worldset):
 i=idx.get(t)
 if i is None: continue
 bc=e=None; calls=[]; local=[]; ok=True
 for l in asm[i:i+80]:
  m=re.match(r'B02:\$([0-9A-Fa-f]{4})\s+(?:[0-9a-f]{2}\s+)+\s*(.*)',l,re.I)
  if not m: continue
  addr=int(m.group(1),16); op=m.group(2).strip()
  if addr!=t and addr in worldset: break
  q=re.match(r'LD BC,\$([0-9A-Fa-f]{4})',op)
  if q: bc=int(q.group(1),16); continue
  q=re.match(r'LD E,\$([0-9A-Fa-f]{2})',op)
  if q: e=int(q.group(1),16); continue
  q=re.match(r'CALL \$([0-9A-Fa-f]{4})',op)
  if q:
   c=int(q.group(1),16); calls.append(c)
   if c==0x6594:
    if bc is None or e is None: ok=False;break
    local.append((bc,e))
   elif c!=0x5FB1: ok=False;break
   continue
  if op.startswith('RET'): break
  if op.startswith('JP '): ok=False;break
 # Need at least one room entry, and no calls except accepted ones.
 if ok and local and all(c in (0x6594,0x5FB1) for c in calls):
  targets.append(t); actions += [(t,p,c) for p,c in local]
  if 0x5FB1 in calls: finalize.append(t)
(root/'src/world_room_callbacks.inc').write_text(''.join(f'{{0x{t:04X}u,0x{p:04X}u,0x{c:02X}u}},\n' for t,p,c in actions))
(root/'src/world_room_callback_targets.inc').write_text(''.join(f'0x{t:04X}u,\n' for t in targets))
(root/'src/world_room_finalize_targets.inc').write_text(''.join(f'0x{t:04X}u,\n' for t in finalize))
print(f'room callbacks: {len(targets)} targets, {len(actions)} entry triggers, {len(finalize)} with $5FB1')
