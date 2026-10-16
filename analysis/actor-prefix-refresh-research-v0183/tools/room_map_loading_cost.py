"""Instruction-derived original2279 tile-map preparation, no VDP wait included."""
def room_map_cost():
 total=4*11+10+7
 for y in range(20):
  total+=7
  for x in range(32):
   tile=sum([11,4,8,4,7,4,4,4,4,4,7,10,11,7,4,11,11,11,10,8])
   tile+=12 if not y&1 else 7+8
   tile+=8+(12 if not x&1 else 7+8)
   tile+=sum([11,7,6,7,10,10])
   total+=17+tile+sum([7,6,7,6,4,4,7])+(12 if x<31 else 7)
  total+=4+4+7+(12 if y<19 else 7)
 total+=4*10+10
 return dict(foreground_tstates=total,tiles=640,scope='Original2279/22E2 builds32x20 tile words from160 metatiles; cost independent of map values. No HUD,VDP transfer or busy wait.')
