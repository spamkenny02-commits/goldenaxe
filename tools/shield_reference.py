"""2346/2E08: hero collision and the successful shield branch.

This reference covers detection/reflection. Native normal-ground hero damage is
validated separately against controlled SMS runs; other terrains remain pending.
"""
from sprite_reference import descriptor


def hero_collision(rom,direction,pose=0):
    table=int.from_bytes(rom[0x300a0+direction*2:0x300a2+direction*2],'little')
    address=int.from_bytes(rom[0x30000+(table&0x3fff)+pose*2:0x30002+(table&0x3fff)+pose*2],'little')
    return rom[0x30001+(address&0x3fff)]


def present_collision_indices(rom,records):
    for slot in range(16):
        off=slot*48;entity=records[off:off+48]
        if entity[0] and entity[3]&1:
            frame,_=descriptor(rom,entity)
            records[off+0x1b:off+0x1d]=frame[1:3]


def reflect(rom,records,x,y,direction,shield,clock,pose=0):
    index=hero_collision(rom,direction,pose)
    if clock&1 or not index:return None
    def box(i):return rom[0x8100+(i*4&255):0x8104+(i*4&255)]
    dx,w,dy,h=box(index)
    left=(x+dx)&255;top=(y+dy)&255
    right=(left+w)&255;bottom=(top+h)&255
    for slot in range(16):
        off=slot*48;e=records[off:off+48]
        if not e[0] or e[6] or not e[3]&2 or not e[0x1c]:continue
        dx,w,dy,h=box(e[0x1c])
        sx=e[0x13]+dx;sy=e[0x11]+dy
        if sx<256 or sy<256:continue
        sx&=255;sy&=255
        if sx>=right or sy>=bottom or sx+w>=256 or sy+h>=256 or sx+w<left or sy+h<top:continue
        records[off+3]|=4
        if not e[3]&16 or shield>3 or rom[0x32269+shield]<e[0x19]:return None
        axis=0x14 if direction<2 else 0x16
        v=int.from_bytes(e[axis:axis+2],'little',signed=True)
        if not v or (v<0 if direction in (0,2) else v>=0):return None
        records[off+axis:off+axis+2]=(-v&65535).to_bytes(2,'little')
        records[off+4]=10;records[off+3]=(e[3]|4)&253
        return slot
    return None
