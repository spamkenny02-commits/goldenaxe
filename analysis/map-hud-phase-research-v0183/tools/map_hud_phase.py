"""Chain graphics,map,HUD and its VBlank wait from one16D0 state."""
from foreground_phase import ForegroundPhase
from world_map_phase import predict_world_map
from graphics_load_phase import execute,ldir,plane_decode
from wait_raster_prediction import predict_save_wait
from room_map_loading_cost import room_map_cost
from hud_loading_cost import hud_cost,health_gauge_cost,magic_gauge_cost,gem_gauge_cost,gold_gauge_cost
from map_hud_loading_cost import map_hud_cost

def room_map(cpu):
 before=cpu.foreground_tstates;execute(cpu,[11]*4+[10,7])
 for y in range(20):
  cpu.execute(7)
  for x in range(32):
   execute(cpu,[17,11,4,8,4,7,4,4,4,4,4,7,10,11,7,4,11,11,11,10,8])
   execute(cpu,[12] if not y&1 else [7,8]);cpu.execute(8)
   execute(cpu,[12] if not x&1 else [7,8])
   execute(cpu,[11,7,6,7,10,10,7,6,7,6,4,4,7,12 if x<31 else 7])
  execute(cpu,[4,4,7,12 if y<19 else 7])
 execute(cpu,[10]*5);assert cpu.foreground_tstates-before==room_map_cost()['foreground_tstates']

def gauge(cpu,value,maximum,magic=False):
 before=cpu.foreground_tstates;original=value
 execute(cpu,[10,10,20,4,4,4,4,7,4] if magic else [10,10,13,4,13,4,4,4,7,4])
 count=(maximum>>3)&31 or 256
 for n in range(count):
  execute(cpu,[4,7,4])
  if value>=8:
   value-=8;execute(cpu,[7,7,6,7,6,13 if n+1<count else 8])
   if n+1==count:cpu.execute(10);break
  else:
   cpu.execute(12)
   if magic:
    cpu.execute(4)
    for m in range(n,count):execute(cpu,[7,6,7,6,13 if m+1<count else 8])
   else:
    execute(cpu,[7,8,7,8,7,6,7,6,13 if n+1<count else 8])
    for m in range(n+1,count):execute(cpu,[10,6,7,6,13 if m+1<count else 8])
   cpu.execute(10);break
 assert cpu.foreground_tstates-before==(magic_gauge_cost if magic else health_gauge_cost)(original,maximum)

def hud(cpu,context):
 health,hmax,magic,mmax,gold=context[:5];gems=sum((1<<n) if context[5+n]&128 else 0 for n in range(9));before=cpu.foreground_tstates
 execute(cpu,[7,13,10,10,17,7]);plane_decode(cpu,0x126ab,0xdb00,2)
 execute(cpu,[10,7])
 for n in range(128):execute(cpu,[7,7,7,6,7,7,7,6,13 if n<127 else 8])
 execute(cpu,[10,10,10,17])
 for row in range(2):
  execute(cpu,[11,11,4])
  for col in range(4):execute(cpu,[16,13 if col<3 else 8])
  execute(cpu,[10,10,7,4,4,12,4,12 if row==0 else 7])
 cpu.execute(10);cpu.execute(7)
 for number in range(4):
  execute(cpu,[11,4,17,7,4,10,15,11,4,4,12,7,6,7,4,4])
  body_before=cpu.foreground_tstates
  if number==0:
   execute(cpu,[10,14,7])
   for n in range(9):
    cpu.execute(12)
    execute(cpu,[7,7,19,19,11,14,19,19] if gems&(1<<n) else [12])
    execute(cpu,[6,10,10,13 if n<8 else 8])
   cpu.execute(10);assert cpu.foreground_tstates-body_before==gem_gauge_cost(gems)
  elif number==1:
   execute(cpu,[13,10,10,7,17]);hundreds,rest=divmod(gold,100)
   for pos,q in enumerate([hundreds,rest//10]):
    if pos:execute(cpu,[7,17])
    cpu.execute(7)
    for _ in range(q):execute(cpu,[4,4,12])
    execute(cpu,[4,4,7,4,7,6,10,6,10])
   execute(cpu,[7,7,12,6,10,6,10]);assert cpu.foreground_tstates-body_before==gold_gauge_cost(gold)
  elif number==2:gauge(cpu,magic,mmax,True)
  else:gauge(cpu,health,hmax)
  execute(cpu,[14,10,10,13 if number<3 else 8])
 execute(cpu,[10,7])
 for n in range(128):execute(cpu,[7,7,7,6,6,13 if n<127 else 8])
 cpu.execute(10);assert cpu.foreground_tstates-before==hud_cost(cpu.rom,health,hmax,magic,mmax,gold,gems)['foreground_tstates']

def predict_map_hud(rom,phase,ram,sound,room,context):
 assert len(context)==16 and context[15]<4
 points=predict_world_map(rom,phase,ram,sound,room);base=points[0x24bc]
 cpu=ForegroundPhase(rom,base['phase'],base['ram'],base['sound'])
 def combine(r,b):
  r=dict(r);r['wall_master_cycles']+=b['wall_master_cycles'];r['foreground_tstates']+=b['foreground_tstates'];r['IRQ_tstates']+=b['IRQ_tstates'];r['events']=b['events']+[dict(e,entry_offset_master=e['entry_offset_master']+b['wall_master_cycles']) for e in r['events']];return r
 def checkpoint(pc):cpu.checkpoint();points[pc]=combine(cpu.result(),base)
 execute(cpu,[17,17]);room_map(cpu);checkpoint(0x1de5)
 cpu.execute(17);hud(cpu,context);checkpoint(0x1de8)
 execute(cpu,[17,11,11,11,11,17]);checkpoint(0xb95)
 wait=predict_save_wait(rom,cpu.phase(),cpu.ram,cpu.sound);points[0xbb3]=combine(wait,points[0xb95]);base=points[0xbb3]
 cpu=ForegroundPhase(rom,base['phase'],base['ram'],base['sound'])
 execute(cpu,[10,13,14,14,10,10,10,10,4,4,10,10,10,10,10]);checkpoint(0x22a3)
 cpu.execute(4,'DI');execute(cpu,[4,11,7,11,10,10,7])
 for row in range(12):
  for col in range(128):execute(cpu,[16,13 if col<127 else 8])
  execute(cpu,[4,10])
 cpu.execute(11,'status');cpu.execute(4,'EI');execute(cpu,[10]*5);checkpoint(0x1deb)
 execute(cpu,[10,10,10]);ldir(cpu,16);execute(cpu,[13,4,10,11,4,4,12,7,6,7,4,10,16,13,4])
 if not context[14]:cpu.execute(12)
 else:
  execute(cpu,[7,13,4,4]);execute(cpu,[12] if cpu.ram[0x2f]&2 else [7,10,16])
 execute(cpu,[13,7]);execute(cpu,[12] if cpu.ram[0x2f]&2 else [7,4]);execute(cpu,[13,10]);checkpoint(0x24bf)
 h,hm,m,mm,g=context[:5];gems=sum((1<<n) if context[5+n]&128 else 0 for n in range(9))
 expected=17+map_hud_cost(rom,h,hm,m,mm,g,gems,base['ram'][0x2f],context[14])['foreground_excluding_wait_save_spin']+wait['foreground_tstates']
 assert points[0x24bf]['foreground_tstates']-points[0x24bc]['foreground_tstates']==expected
 return points
