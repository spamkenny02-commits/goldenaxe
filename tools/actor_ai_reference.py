"""Ground enemy states 2/4/6/8, with explicit refresh-register inputs."""
import hashlib,json
from actor_reference import ROOT,spawn_candidate
from actor_tick_reference import common_tick
from extract_world import initial_room


def blocked(entity,tilemap,direction):
    x,y=entity[0x13],entity[0x11]
    if direction==0 and y<25:return True
    if direction==1 and y>=152:return True
    if direction==2 and x<17:return True
    if direction==3 and x>=232:return True
    dx,dy=[(-8,-16),(-8,0),(-16,-8),(8,-8)][direction]
    offset=(((y+dy)&248)*8)+(((x+dx)&248)>>2)
    first=tilemap[offset+1]
    second=tilemap[offset+3] if direction<2 else first
    if entity[0]==0x34:return (first&second&0xc0)!=0xc0
    return bool((first|second)&0xa0)


def behavior(rom,entity,tilemap,refresh,cells=None,hero_x=0,hero_y=0,frame=0,slot=0):
    state=entity[1]
    if state==0:
        if cells is None or frame&7!=slot&7:return
        value=refresh()
        if spawn_candidate(rom,entity,cells,hero_x,hero_y,frame,slot,value,0):
            entity[10]=refresh()&3
            entity[8:10]=bytes.fromhex('fa84');entity[13]=16;entity[12]=4;entity[1]=2
        return
    if state==2:
        if entity[11]!=3:return
        entity[11]=0;entity[8:10]=bytes.fromhex('2486');entity[12]=2
        entity[0x20]=rom[0x87c4+entity[0]-0x26]
        entity[1]=state=4
    if state==4:
        direction=refresh()&3
        if blocked(entity,tilemap,direction):return
        entity[10]=direction
        state=6
    if state==6:
        pointer=0x87c7+(entity[0]-0x26)*2
        sequence=int.from_bytes(rom[pointer:pointer+2],'little')
        entity[4]=rom[sequence]
        offset=sequence+1+entity[10]*4
        entity[0x14:0x18]=rom[offset:offset+4]
        entity[13]=entity[4];entity[1]=8
        return
    if state==8 and not entity[4]:
        if entity[0x20]==1:
            entity[0x20]=0;entity[1]=4
        elif blocked(entity,tilemap,entity[10]) or not refresh()&15:
            entity[1]=4
        else:entity[1]=6


def main():
    rom=(ROOT/'input/original.sms').read_bytes()
    tilemap=initial_room(rom,0xa4)[3]
    source=ROOT/'validation/sms-vertical-check'
    entity=bytearray((source/'ram_03101.bin').read_bytes()[0x600:0x630])
    decisions=[]
    def refresh():
        # Explicit direction input for the one decision in this interval.
        decisions.append(0)
        return 0
    for frame in range(3102,3161):
        behavior(rom,entity,tilemap,refresh);common_tick(entity)
        expected=(source/f'ram_{frame:05}.bin').read_bytes()[0x600:0x630]
        assert entity[:0x1b]+entity[0x1d:]==expected[:0x1b]+expected[0x1d:], (frame,entity.hex(),expected.hex())
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),checked_frames=59,
                explicit_refresh_inputs=decisions,logic_bytes_per_frame=46,
                first_actor_emergence_and_walk_exact=True,
                original_refresh_stream_reproduced=False,spawn_and_damage_ported=False)
    (ROOT/'analysis/actor_ai_reference.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
