"""ROM semantic reference for types 20..22 and exterior projectiles 10..12."""
from actor_ai_reference import behavior,blocked
from actor_tick_reference import common_tick


def ranged(rom,entity,tilemap,refresh,hero_x,hero_y,records):
    state=entity[1]
    if state==2:
        if entity[11]!=3:return
        entity[11]=0;entity[8:10]=bytes.fromhex('2e85')
        entity[13]=10;entity[12]=2;entity[1]=state=4
    if state==4:
        direction=refresh()&3
        if blocked(entity,tilemap,direction):return
        entity[10]=direction;state=6
    if state==6:
        entity[4]=rom[0x85d9]
        start=0x85da+entity[10]*4
        entity[0x14:0x18]=rom[start:start+4];entity[1]=8;return
    if state==8:
        if entity[4]:return
        if blocked(entity,tilemap,entity[10]):entity[1]=4;return
        value=refresh()&15
        if value<2:entity[1]=4;return
        if value<8:entity[1]=6;return
        if entity[0x13]&240==hero_x&240:entity[10]=0 if hero_y<entity[0x11] else 1
        elif entity[0x11]&240==hero_y&240:entity[10]=2 if hero_x<entity[0x13] else 3
        else:entity[1]=6;return
        entity[0x14:0x18]=bytes(4);entity[4]=16;entity[1]=10;return
    if state==10 and not entity[4]:
        for slot in range(8,16):
            start=slot*0x30
            if records[start]:continue
            records[start]=rom[0x85d6+entity[0]-0x20]
            for field in (2,0x13,0x11,10):records[start+field]=entity[field]
            break
        entity[4]=8;entity[1]=12;return
    if state==12 and not entity[4]:entity[1]=4


def projectile(rom,entity):
    actor_type=entity[0]
    if not entity[1]:
        start=[0x3e53,0x3e76,0x3eb6][actor_type-0x10]
        entity[8:10]=rom[start:start+2];entity[0x19]=rom[start+2]
        entity[0x11]=(entity[0x11]+rom[start+3])&255
        entity[12:14]=rom[start+4:start+6]
        start+=6+entity[10]*4;entity[0x14:0x18]=rom[start:start+4]
        entity[1]=2;entity[4]=128;entity[3]=0x13;return
    if entity[0x11]<8 or entity[0x11]>=152 or entity[0x13]<8 or entity[0x13]>=248 or not entity[4]:
        entity[:]=bytes(0x30)
    if actor_type==0x12:
        phase=entity[14]+1
        if phase>=2:phase=0
        entity[14]=phase
        if not phase:
            pose=entity[11]+1;entity[11]=1 if pose>=4 else pose


def step_actors(rom,records,tilemap,cells,hero_x,hero_y,frame,refresh):
    for slot in range(16):
        start=slot*0x30;entity=bytearray(records[start:start+0x30])
        if not entity[0]:continue
        if not entity[6]:
            if 0x26<=entity[0]<=0x28 or (0x20<=entity[0]<=0x22 and not entity[1]):
                behavior(rom,entity,tilemap,refresh,cells,hero_x,hero_y,frame,slot)
            elif 0x20<=entity[0]<=0x22:ranged(rom,entity,tilemap,refresh,hero_x,hero_y,records)
            elif 0x10<=entity[0]<=0x12:projectile(rom,entity)
        common_tick(entity);records[start:start+0x30]=entity
