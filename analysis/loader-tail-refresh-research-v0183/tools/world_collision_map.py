"""Class0 collision tilemap from original ROM, room and persisted bit0 only."""
from actor_loading_cost import rle_cost
from extract_title import rle_planes
from world_map_loading_cost import ROOMS

def world_collision_map(rom,room,flags=1):
 assert room in ROOMS and flags&1
 meta=bytearray(2048);source=rle_cost(rom,0x3c010,0x4000)['source_end'];rle_planes(rom,source,meta,0,2)
 for target in [0x1c0,0x1f0]:meta[target:target+8]=meta[0x98:0xa0]
 p=0x81fc;end=0x400
 while rom[p]<128:meta[end:end+8]=meta[rom[p]*8:rom[p]*8+8];p+=1;end+=8
 p+=1
 for n in range(0x401,end,2):meta[n]=(meta[n]&31)|rom[p];p+=1
 bank=8+(room>>7);table=bank*0x4000+(room*2&255);address=int.from_bytes(rom[table:table+2],'little');source=bank*0x4000+(address&0x3fff);cells=bytearray(512);rle_planes(rom,source,cells,0,1)
 p=0xbb62
 while rom[p] and rom[p]!=room:p+=4
 record=rom[p+1:p+4] if rom[p] else rom[0x199e:0x19a1];coordinate,kind=record[1:3];assert kind in [0,4]
 cells[coordinate]=0 if kind==0 else 4
 target=coordinate+16
 for n in range(4):
  if cells[target]==rom[0x1b05+n*2]:cells[target]=rom[0x1b06+n*2];break
 tilemap=bytearray(1280)
 for y in range(20):
  for x in range(32):
   cell=cells[(y//2)*16+x//2];a=cell*8+(y&1)*4+(x&1)*2;b=(y*32+x)*2;tilemap[b:b+2]=meta[a:a+2]
 return dict(tilemap=bytes(tilemap),cells=bytes(cells),metatiles=bytes(meta),metadata=list(record))
