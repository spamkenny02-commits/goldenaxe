"""Instruction-derived original1E4E HUD preparation, including variable gauges."""
from ram_plane_loading_cost import ram_plane_cost

def health_gauge_cost(value,maximum):
 total=sum([10,10,13,4,13,4,4,4,7,4]);count=(maximum>>3)&31
 count=count or 256
 for n in range(count):
  total+=4+7+4
  if value>=8:
   value-=8;total+=7+7+6+7+6+(13 if n+1<count else 8)
   if n+1==count:return total+10
  else:
   total+=12+sum([7,8,7,8,7,6,7,6])+(13 if n+1<count else 8)
   if n+1==count:return total+10
   for m in range(n+1,count):total+=10+6+7+6+(13 if m+1<count else 8)
   return total+10

def magic_gauge_cost(value,maximum):
 total=sum([10,10,20,4,4,4,4,7,4]);count=(maximum>>3)&31
 count=count or 256
 for n in range(count):
  total+=4+7+4
  if value>=8:
   value-=8;total+=7+7+6+7+6+(13 if n+1<count else 8)
   if n+1==count:return total+10
  else:
   total+=12+4
   for m in range(n,count):total+=7+6+7+6+(13 if m+1<count else 8)
   return total+10

def gem_gauge_cost(mask):
 total=10+14+7
 for n in range(9):
  total+=12+(7+sum([7,19,19,11,14,19,19]) if mask&(1<<n) else 12)
  total+=6+10+10+(13 if n<8 else 8)
 return total+10

def gold_gauge_cost(value):
 hundreds,remainder=divmod(value,100);tens=remainder//10
 digit=lambda q:7+20*q+15+4+7+6+10+6+10
 return sum([13,10,10,7,17,digit(hundreds),7,17,digit(tens),7,7,12,6,10,6,10])

def hud_cost(rom,health,health_max,magic,magic_max,gold,gems=0):
 parts={}
 parts['decode']=sum([7,13,10,10,17,7])+ram_plane_cost(rom,0x126ab,0xdb00,2)['tstates']
 parts['tile_offsets']=10+7+128*sum([7,7,7,6,7,7,7,6,13])-5
 icon=2*sum([11,11,4,4*(16+13)-5,10,10,7,4,4,12,4,12])-5+10
 parts['item_icon']=10+10+10+17+icon
 bodies=[gem_gauge_cost(gems),gold_gauge_cost(gold),magic_gauge_cost(magic,magic_max),health_gauge_cost(health,health_max)]
 dispatch=sum([7,4,10,15,11,4,4,12,7,6,7,4,4,14,10])
 parts['gauges']=7+sum(11+4+17+dispatch+body+10+(13 if n<3 else 8) for n,body in enumerate(bodies))
 parts['priority_attributes']=10+7+128*sum([7,7,7,6,6,13])-5+10
 return dict(foreground_tstates=sum(parts.values()),components=parts,scope='Complete original1E4E,0BFE/0C00,7357,1EA1 and four gauges; allbyte health/magic/gold and nine gem flags. No VDP transfer or wait.')
