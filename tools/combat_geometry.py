"""Controller geometry from the checked native/original collision tables.

Offsets are in the original order: C313/X first, C311/Y second. Axe-2
weapon boxes come from bank-12 metadata rooted at $80B8, poses 4..7.
This module reads geometry only; it never writes game state.
"""
from pathlib import Path
import re

BOXES=tuple(tuple(int(v,16) for v in re.findall(r'0x([0-9A-Fa-f]+)',line))
            for line in (Path(__file__).resolve().parents[1]/'src/hitboxes.inc').read_text().splitlines())
AXE2=((14,15,16,17),(18,19,20,21),(16,22,18,23),(20,24,14,25))


def rect(position, box):
    a,w,b,h=BOXES[box]
    x,y=position
    return x+(a if a<128 else a-256),y+(b if b<128 else b-256),w,h


def overlaps(source, target):
    x,y,w,h=source;tx,ty,tw,th=target
    # $2346 accepts target's upper endpoint equal to source's lower endpoint.
    return w>0 and h>0 and tw>0 and th>0 and tx<x+w and tx+tw>=x and ty<y+h and ty+th>=y


def axe_openings(hero, enemy, source_box, target_box, margin=4):
    if not source_box or not target_box:return ()
    hx,hy,w,h=rect(hero,5)
    body=(hx-margin,hy-margin,w+2*margin,h+2*margin)
    if overlaps(body,rect(enemy,target_box)):return ()
    enemy_body=rect(enemy,source_box)
    return tuple(d for d,boxes in enumerate(AXE2)
                 if any(overlaps(enemy_body,rect(hero,b)) for b in boxes))
