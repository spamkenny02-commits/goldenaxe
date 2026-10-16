"""Instruction-derived foreground work of SMS pattern RLE032A and remap1D0D.

Counts Z80 T states from the translated loops, excluding VDP contention and IRQs.
This is resource metadata, never captured emulator state or runtime Z80 execution.
"""
from actor_reference import ROOT

def rle_cost(rom,source,destination=0x6000):
 start=source;total=7+4;last=destination
 for plane in range(4):
  dst=destination+plane;total+=22
  while True:
   command=rom[source];source+=1;total+=7+6+4
   if not command:total+=12;break
   total+=7+4+8+4+4;count=(command&127) or 256;literal=bool(command&128)
   for n in range(count):
    total+=59+7+11+4+(7 if literal else 12)+(6 if literal else 0)+4+4+4+4
    if (dst&255)+4<256:total+=12
    else:total+=7+4
    dst+=4;total+=13 if n+1<count else 8
    if literal:source+=1
   total+=4+(12 if literal else 7+6+12)
   if not literal:source+=1
  last=dst;total+=20+10+6+10+(13 if plane<3 else 8)
 total+=20+6+4+4+4+(12 if ((last+1)&255)>=4 else 7+4)+10
 return dict(tstates=total,source_end=source,decoded_bytes=(last-3)-destination,packed_bytes=source-start)

def remap_cost(byte_count,destination=0x6000,remap=0x20,ini_tstates=16):
 assert byte_count%32==0 and byte_count>0
 # 1D0D..1D34, including 16-byte palette table copy.
 total=33+4+4+15+4+4+10+4+4+(12 if 0xa2+remap<256 else 7+4)+11+4+10+10+10+(15*21+16)+4+4+3*(4+8)
 tiles=byte_count//32
 for tile in range(tiles):
  total+=11+4+10+4+8+7+12+12+10+10+(31*(ini_tstates+13)+ini_tstates+8)+8+4+12+12+4+10+10+4
  # Eight rows: unpack 8 color indices, then reconstruct four 8-bit planes.
  total+=8*(7+(7*131+126)+4+4*(7+(7*36+31)+11)+(4+7+4+7+10))
  total+=4+7+4+4
  total+=12 if (destination&255)+32<256 else 7+4
  destination+=32;total+=13 if tile+1<tiles else 8
 return total+10+10+10+10

def resource_cost(rom,entry):
 destination=0x6000+entry['tile_base']*32
 rle=rle_cost(rom,entry['rom_start'],destination)
 assert rle['source_end']==entry['rom_end']
 assert rle['decoded_bytes']==entry['tile_count']*32,(entry,rle)
 remap=remap_cost(rle['decoded_bytes'],destination,entry['palette_remap']) if entry['palette_remap'] else 0
 return dict(type=entry['type'],rle_tstates=rle['tstates'],remap_tstates=remap,foreground_graphics_tstates=rle['tstates']+remap,decoded_bytes=rle['decoded_bytes'])

if __name__=='__main__':
 import json
 from actor_reference import load_room_actors
 rom=(ROOT/'input/original.sms').read_bytes()
 print(json.dumps([resource_cost(rom,e) for e in load_room_actors(rom,0xa4)[4]],indent=2))
