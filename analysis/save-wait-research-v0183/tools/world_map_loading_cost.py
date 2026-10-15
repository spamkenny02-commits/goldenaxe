"""Original190B cost for six paid-exit rooms,C0AC0 and C041!=5."""
from ram_plane_loading_cost import ram_plane_cost
from extract_title import rle_planes

ROOMS=[0x1a,0x3c,0x36,0x87,0x6d,0x96]

def tile_patch_cost(coordinate):
 # Original1B0E writes a cell,queues its address and copies two tile rows.
 total=sum([11,11,7,4,7,11,11,11,10,11,11,4,7,4,7,4,11,11,11,4,7,4,4,4,11,10,11,4,16,7,7,4,7,4,7,4,7,4,7,4,16,10])
 total+=4*16+7+4+4
 address=0xd600+(coordinate&0xf0)*8+(coordinate&15)*2+4
 total+=12 if (address&255)+60<256 else 7+4
 return total+4*16+10+10+10

def world_map_cost(rom,room,flags=1):
 assert room in ROOMS
 parts={}
 classify=sum([13,4,7,7,13,7,7,7,13,7,7,7,7,4,13,10])
 bank=8+(room>>7);table=bank*0x4000+(room*2&255)
 pc=int.from_bytes(rom[table:table+2],'little');source=bank*0x4000+(pc&0x3fff)
 parts['decode']=44+17+classify+sum([16,11,4,7,13,7,7,6,7,4,10,7,17])+ram_plane_cost(rom,source,0xdc00,1)['tstates']
 metadata=sum([17,13,4,11,7,13,20,4,4,10,12,10])
 p=0xbb62
 while rom[p] and rom[p]!=room:metadata+=7+4+7+4+7+11+12;p+=4
 if rom[p]:metadata+=7+4+7+4+12+6;record=rom[p+1:p+4]
 else:metadata+=7+4+12+10+12;record=rom[0x199e:0x19a1]
 metadata+=10+3*16+13+4+12
 #1951/195E selects bit0 of this class0 room's flags through C04D=1.
 metadata+=17+sum([16,13,7,12,7,10,4,4,7,4,7,4,4,7,10])
 if flags&1:
  metadata+=17+sum([20,4,7,4,10,10,4,4,12,7,6,7,4,4])
  coordinate=record[1];kind=record[2];assert kind in [0,4]
  metadata+=4+12 if kind==0 else 7
  metadata+=17+tile_patch_cost(coordinate)
  metadata+=sum([10,11,4,7,10,7])
  cells=bytearray(512);rle_planes(rom,source,cells,0,1)
  target=coordinate+16
  for n in range(4):
   metadata+=7+6+10
   if cells[target]==rom[0x1b05+n*2]:
    metadata+=7+tile_patch_cost(target);break
   metadata+=6+(13 if n<3 else 8)
  else:metadata+=10
 else:metadata+=10
 metadata+=sum([4,13,13,7,12,10])
 parts['metadata_and_persistence']=17+metadata
 #1A02:1A30 patches class0 metatiles,C0AC0;1A09 returns for non-BF rooms.
 terrain=sum([13,4,5,13,4,7,10,10,10,11,11,163,10,10,10,163,10])
 parts['terrain_and_special_room']=17+(17+terrain)+17+sum([20,10,4,15,11])+10
 parts['clear_queue_and_return']=10+10+16+4*10+10
 return dict(foreground_tstates=sum(parts.values()),components=parts,metadata=list(record),scope='Six paid-exit destinations,class0,C0AC0,C041!=5,C04D1; all room flag bytes. Real map bytes determine secondary cell transform.')
