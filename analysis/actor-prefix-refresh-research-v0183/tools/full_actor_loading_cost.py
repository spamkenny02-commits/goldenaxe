"""Instruction-derived1780..18E1 model for ordinary non-boss room actor lists."""
from actor_reference import ROOT,load_room_actors
from actor_loading_cost import rle_cost,remap_cost

def full_actor_cost(rom,room,persistence=255):
 raw=list(rom[0x3234e+room*8:0x32356+room*8]);types=[t if persistence&(128>>n) else 0 for n,t in enumerate(raw)]
 parts={}
 parts['clear_and_list']=7+13+10+10+10+10+(766*21+16)+16+33+10+11+14+10+7+8*(7+6+19+15+13)-5
 parts['stats']=14+7+sum(19+7+(12 if t<32 else 7+176)+10+15+13 for t in raw)-5
 parts['persistence']=16+7+7+14+7+sum(8+(12 if persistence&(128>>n) else 7+1054)+10+15+13 for n in range(8))-5
 flags=0
 for t in types:
  if t>=32:flags|=rom[0x320ea+(t-32)*4+3]
 parts['boss_gate']=10+10+4+7+8*(7+11+13)-5+7+(12 if not flags&64 else 7+16+7+10+11+7+4+12)
 count=sum(bool(t) for t in types)
 parts['count']=10+10+10+sum(7+4+(7+4 if t else 12)+11+13 for t in types)-5+4+4+(12 if count else 7+7)+13+14+10
 loaded={};tile=0;graphics=0;resources=[]
 for slot,t in enumerate(types):
  graphics+=19+7+10
  if t>=32:
   graphics+=7+4+4+14+10+19
   if t in loaded:
    previous=types.index(t);graphics+=previous*67+45+19+19
   else:
    graphics+=slot*67+14
    graphics+=sum([19,7,4,7,4,4,11,11,10,11,7,13,7,6,7,6,7,11,7,13,4,7,55,4,8,8,11,11,17])
    descriptor=0x825f+(t-32)*3;packed=rom[descriptor];pc=int.from_bytes(rom[descriptor+1:descriptor+3],'little');start=(packed&15)*0x4000+(pc&0x3fff);destination=0x6000+tile*32
    rle=rle_cost(rom,start,destination);size=rle['decoded_bytes'];remap=remap_cost(size,destination,packed&240,ini_tstates=20) if packed&240 else 0
    graphics+=rle['tstates']+10+10+10+7+(17+remap if remap else 10)+80+4+12
    loaded[t]=tile;tile+=size//32;resources.append(dict(type=t,destination=destination,rle=rle['tstates'],remap=remap))
  graphics+=10+15+4+10
 parts['graphics']=graphics+4+13
 return dict(foreground_tstates=sum(parts.values()),components=parts,resources=resources,limit='Ordinary rooms only; boss-defeat suppression branch assumes the defeat byte is zero. IRQ/VDP contention excluded; GX INI20 behavior modeled.')

if __name__=='__main__':
 import json
 rom=(ROOT/'input/original.sms').read_bytes()
 print(json.dumps(full_actor_cost(rom,150),indent=2))
