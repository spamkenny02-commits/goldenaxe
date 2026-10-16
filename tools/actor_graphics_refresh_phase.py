"""Original actor pattern allocation, RLE and palette remap instruction phases."""
from actor_prefix_refresh_phase import predict_actor_prefix
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_prefix_phase import pattern_rle
from graphics_load_phase import execute,ldir
from actor_loading_cost import rle_cost,remap_cost
from full_actor_loading_cost import full_actor_cost

def remap_phase(cpu,size,destination,remap):
 before=cpu.foreground_tstates
 execute(cpu,[11]*3+[4,4]);cpu.execute(15,'M1_2');execute(cpu,[4,4,10,4,4]);execute(cpu,[12] if 0xa2+remap<256 else [7,4]);execute(cpu,[11,4,10,10,10]);ldir(cpu,16);execute(cpu,[4,4])
 for _ in range(3):cpu.execute(4);cpu.execute(8,'M1_2')
 for tile in range(size//32):
  execute(cpu,[11,4,10]);cpu.execute(4,'DI');cpu.execute(8,'M1_2');cpu.execute(7);cpu.execute(12,'M1_2');cpu.execute(12,'M1_2');execute(cpu,[10,10])
  for n in range(32):cpu.execute(20);cpu.execute(13 if n<31 else 8)
  cpu.execute(8,'M1_2');cpu.execute(4);cpu.execute(12,'M1_2');cpu.execute(12,'M1_2');cpu.execute(4,'EI');execute(cpu,[10,10,4])
  for row in range(8):
   cpu.execute(7)
   for bit in range(8):
    execute(cpu,[4,4])
    for plane in range(4):
     cpu.execute(15,'M1_2');cpu.execute(4)
     if plane<3:cpu.execute(4)
    execute(cpu,[4,7,7,4,13 if bit<7 else 8])
   cpu.execute(4)
   for plane in range(4):
    cpu.execute(7)
    for bit in range(8):
     if not plane&1:cpu.execute(4)
     cpu.execute(15,'M1_2');cpu.execute(4)
     if plane&1:cpu.execute(4)
     cpu.execute(13 if bit<7 else 8)
    cpu.execute(11)
   execute(cpu,[4,7,4,7,10])
  execute(cpu,[4,7,4,4]);execute(cpu,[12] if (destination&255)+32<256 else [7,4]);destination+=32;cpu.execute(13 if tile+1<size//32 else 8)
 execute(cpu,[10]*4);assert cpu.foreground_tstates-before==remap_cost(size,destination-size,remap,ini_tstates=20)

def actor_graphics_work(rom,end,room,persistence,cpu_class=GraphicsPrefixRefreshPhase):
 base=end['prediction'];actors=bytearray(end['actors'])
 class ScopedPhase(cpu_class):entry_refresh=base['refresh']
 cpu=ScopedPhase(rom,base['phase'],base['ram'],base['sound']);points=[];tile=0
 def checkpoint(pc):
  cpu.checkpoint();p=cpu.result()
  for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:p[k]+=base[k]
  p['events']=base['events']+[dict(e,entry_offset_master=e['entry_offset_master']+base['wall_master_cycles']) for e in p['events']]
  points.append(dict(pc=pc,prediction=p,actors=bytes(actors),allocated=tile))
 execute(cpu,[14,10])
 for slot in range(8):
  t=actors[slot*48];execute(cpu,[19,7,10])
  if t>=32:
   execute(cpu,[7,4,4,14,10,19]);previous=next((n for n in range(slot) if actors[n*48]==t),None)
   for n in range(previous if previous is not None else slot):execute(cpu,[4,10,19,7]);cpu.execute(15,'M1_2');cpu.execute(12)
   if previous is not None:execute(cpu,[4,10,19,12,19,19]);actors[slot*48+2]=actors[previous*48+2]
   else:
    execute(cpu,[4,10,19]);actors[slot*48+2]=tile
    execute(cpu,[7,4,7,4,4,11,11,10,11,7,13,7,6,7,6,7,11,7,13,4,7]+[11]*5+[4]);cpu.execute(8,'M1_2');cpu.execute(8,'M1_2');execute(cpu,[11,11]);checkpoint(0x18ac);cpu.execute(17)
    descriptor=0x825f+(t-32)*3;packed=rom[descriptor];address=int.from_bytes(rom[descriptor+1:descriptor+3],'little');source=(packed&15)*0x4000+(address&0x3fff);destination=0x6000+tile*32
    resource=rle_cost(rom,source,destination);pattern_rle(cpu,source,destination);checkpoint(0x18af);execute(cpu,[10,10,10,7])
    if packed&240:cpu.execute(17);remap_phase(cpu,resource['decoded_bytes'],destination,packed&240)
    else:cpu.execute(10)
    checkpoint(0x18b7)
    for n in range(10):cpu.execute(8,'M1_2')
    tile=(tile+resource['decoded_bytes']//32)&255;execute(cpu,[4,12])
  cpu.execute(10);cpu.execute(15,'M1_2');execute(cpu,[4,10])
 execute(cpu,[4,13]);checkpoint(0x18e1)
 assert cpu.foreground_tstates==24+full_actor_cost(rom,room,persistence)['components']['graphics']
 return dict(graphics_points=points)

def predict_actor_graphics(rom,phase,ram,sound,room,hud_context,refresh,history,flags):
 prior=predict_actor_prefix(rom,phase,ram,sound,room,hud_context,refresh,history,flags)
 result=actor_graphics_work(rom,prior['actor_points'][-1],room,prior['persistence']);result['prior']=prior;return result
