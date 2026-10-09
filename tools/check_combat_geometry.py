#!/usr/bin/env python3
"""Verify controller collision/axe metadata against the private original ROM."""
import argparse
import hashlib
from combat_geometry import BOXES, AXE2
from embed_rom import REFERENCE_SHA256


def validate(data):
    if len(data)!=262144 or hashlib.sha256(data).hexdigest()!=REFERENCE_SHA256:
        raise ValueError('Combat geometry requires the verified original ROM revision')
    assert data[2*16384+0x100:2*16384+0x1C0]==bytes(v for box in BOXES for v in box)
    def byte(a):
        return data[a if a<0x8000 else 12*16384+a-0x8000]
    def word(a):return byte(a)|byte(a+1)<<8
    for direction,boxes in enumerate(AXE2):
        frames=word(0x80B8+direction*2)
        for pose,box in zip(range(4,8),boxes):
            record=word(frames+pose*2)
            assert byte(record+1)==5 and byte(record+2)==box
    return 'Combat geometry: original 48 hitboxes and 16 axe-2 poses match'


if __name__=='__main__':
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    print(validate(parser.parse_args().rom.read_bytes()))
