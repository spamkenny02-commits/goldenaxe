"""Semantic reference for normal-ground hero movement, Z80 3295..33DA/26E5.

ROM map, collision attributes and velocity tables are inputs; captured RAM is
only read by the comparison, never to drive the reference state.
"""
from dataclasses import dataclass
from pathlib import Path
import json
from extract_world import initial_room,ROOT

@dataclass
class Hero:
    y:int=0x7000
    x:int=0x8800
    direction:int=1
    animation:int=0
    counter:int=0
    dy:int=0
    dx:int=0
    pending:int=0

def collision_cache(tilemap,hero):
    # 230E followed by 2CD4: 4 columns x 3 rows around position-12.
    y=((hero.y>>8)-12)&255;x=((hero.x>>8)-12)&255
    offset=(y&248)*8+((x>>2)&62)
    values=[]
    for row in range(3):
        for column in range(4):
            p=offset+row*64+column*2
            high=tilemap[p+1] if p+1<len(tilemap) else 128
            if high&32:high|=128 # 2D01: no water-crossing equipment initially
            values.append(high)
    return values

def choose_collision_direction(direction,cache):
    # Literal translation of the original sliding branches, using word indices.
    wall=lambda n:bool(cache[n]&128)
    if direction==0:
        if not wall(1):return 2 if wall(2) and not wall(4) else (None if wall(2) else 0)
        if wall(2) or wall(7):return None
        return 3
    if direction==1:
        if not wall(10):return (None if wall(7) else 3) if wall(9) else 1
        if wall(9) or wall(4):return None
        return 2
    if direction==2:
        if not wall(4):return 2
        if not any(wall(n) for n in (0,1,2)):return 0
        if any(wall(n) for n in (8,9,10)):return None
        return 1
    if not wall(7):return 3
    if not any(wall(n) for n in (3,2,1)):return 0
    if any(wall(n) for n in (11,10,9)):return None
    return 1

def step(hero,buttons,tilemap,rom):
    if hero.counter==0:
        hero.dy=hero.dx=0
        previous=hero.direction
        if hero.pending&128:
            previous=hero.pending&3;hero.pending=previous
        preferred=buttons&(1<<previous)
        requested=preferred or buttons
        direction=next((n for n in range(4) if requested&(1<<n)),None)
        if direction is not None:
            hero.direction=direction
            hero.counter=rom[0x33db]
            accepted=choose_collision_direction(direction,collision_cache(tilemap,hero))
            if accepted is not None:
                if direction!=accepted:hero.pending=direction|128
                hero.direction=accepted
                address=0x33dc+accepted*4
                hero.dy=int.from_bytes(rom[address:address+2],'little',signed=True)
                hero.dx=int.from_bytes(rom[address+2:address+4],'little',signed=True)
            hero.animation=(hero.animation+1)&3
    if hero.counter:
        hero.counter-=1
        hero.y=(hero.y+hero.dy)&65535;hero.x=(hero.x+hero.dx)&65535
        if hero.counter==0:hero.y&=0xff00;hero.x&=0xff00

def main():
    rom=(ROOT/'input/original.sms').read_bytes();tilemap=initial_room(rom)[3]
    folder=ROOT/'validation/sms-movement'
    capture=json.loads((folder/'capture.json').read_text())
    pressed=capture['presses'];mapping={4:1,5:2,6:4,7:8}
    hero=Hero();differences=[];collisions=0
    for frame in range(2500,capture['frames']+1):
        buttons=sum(mapping[key] for a,b,key in pressed if a<=frame<=b and key in mapping)
        before=hero.x,hero.y
        step(hero,buttons,tilemap,rom)
        if buttons and (hero.x,hero.y)==before:collisions+=1
        path=folder/f'ram_{frame:05d}.bin'
        if not path.exists():continue
        ram=path.read_bytes()
        actual=(int.from_bytes(ram[0x310:0x312],'little'),int.from_bytes(ram[0x312:0x314],'little'),ram[0x30a],ram[0x30b],ram[0x304])
        expected=(hero.y,hero.x,hero.direction,hero.animation,hero.counter)
        if actual!=expected:differences.append((frame,actual,expected))
    report={'frames_compared':len(capture['captures']),'state_fields':['y','x','direction','animation','remaining_move_frames'],
            'different_frames':len(differences),'stationary_frames_with_direction_held':collisions,
            'scope':'Normal-ground motion, collision and sliding in room 0095; excludes other hero states.'}
    print(json.dumps(report,indent=2));print(differences[:12])
    (ROOT/'analysis/movement_reference.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not differences

if __name__=='__main__':main()
