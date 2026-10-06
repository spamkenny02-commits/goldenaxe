#!/usr/bin/env python3
from pathlib import Path
import sys
rom=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms').read_bytes()
out=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/gaw_decomp_phase7/src')
out.mkdir(parents=True,exist_ok=True)

def records_until_zero(name, base, width=4):
    vals=[]; p=base
    while True:
        rec=rom[p:p+width]
        if len(rec)!=width: raise SystemExit(f'truncated {name}')
        vals.append(rec); p+=width
        if rec[0]==0: break
    lines=[]
    for r in vals: lines.append('    {'+','.join(f'0x{x:02X}' for x in r)+'},')
    (out/name).write_text('\n'.join(lines)+'\n')
    return len(vals)

# $3620: [source tile, replacement, optional tile one row below, replacement].
records_until_zero('player_world_action_tiles.inc',0x3620,4)
# Bank 2 event records selected by $1976. Physical offsets happen to equal these
# CPU addresses in this 256 KiB linear dump (bank 2 occupies $8000-$BFFF).
records_until_zero('world_events_overworld.inc',0xBB62,4)
records_until_zero('world_events_interior.inc',0xBD1F,4)
print('phase7 tables generated')
