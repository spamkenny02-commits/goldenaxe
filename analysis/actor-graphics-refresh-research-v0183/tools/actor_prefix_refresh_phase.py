"""Original actor list/stats/persistence/count phase before pattern allocation."""
from history_refresh_phase import predict_history
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_load_phase import execute,ldir
from full_actor_loading_cost import full_actor_cost

def actor_prefix_work(rom,base,room,persistence,cpu_class=GraphicsPrefixRefreshPhase):
 class ScopedPhase(cpu_class):entry_refresh=base['refresh']
 cpu=ScopedPhase(rom,base['phase'],base['ram'],base['sound']);actors=bytearray(768);raw=rom[0x3234e+room*8:0x32356+room*8];points=[];active=0
 def checkpoint(pc):
  cpu.checkpoint();p=cpu.result()
  for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:p[k]+=base[k]
  p['events']=base['events']+[dict(e,entry_offset_master=e['entry_offset_master']+base['wall_master_cycles']) for e in p['events']]
  points.append(dict(pc=pc,prediction=p,actors=bytes(actors),active_count=active if pc==0x1853 else None))
 def add_ix():cpu.execute(15,'M1_2')
 execute(cpu,[7,13,10,10,10,10]);ldir(cpu,767);cpu.execute(16,'M1_1');execute(cpu,[11,11,11,10,11,14,10,7])
 for n,t in enumerate(raw):execute(cpu,[7,6,19]);actors[n*48]=t;add_ix();cpu.execute(13 if n<7 else 8)
 checkpoint(0x17ae);execute(cpu,[14,7])
 for n,t in enumerate(raw):
  execute(cpu,[19,7]);cpu.execute(12 if t<32 else 7)
  if t>=32:
   execute(cpu,[4,7,11,11,10,11,7,19,6,7,19,6,7,19,6,7,19]);stats=rom[0x320ea+(t-32)*4:0x320ee+(t-32)*4];actors[n*48+24:n*48+27]=stats[:3];actors[n*48+3]=stats[3]
  cpu.execute(10);add_ix();cpu.execute(13 if n<7 else 8)
 checkpoint(0x17de);cpu.execute(16,'M1_1');execute(cpu,[7,7,14,7])
 for n in range(8):
  cpu.execute(8,'M1_2');cpu.execute(12 if persistence&(128>>n) else 7)
  if not persistence&(128>>n):
   cpu.execute(4);cpu.execute(15,'M1_2');execute(cpu,[10,4,4,6,10,7]);ldir(cpu,47);cpu.execute(4);cpu.execute(8,'M1_2');actors[n*48:(n+1)*48]=bytes(48)
  cpu.execute(10);add_ix();cpu.execute(13 if n<7 else 8)
 checkpoint(0x1805);execute(cpu,[10,10,4,7])
 for n in range(8):execute(cpu,[7,11,13 if n<7 else 8])
 bits=0
 for n in range(8):bits|=actors[n*48+3]
 assert not bits&64,'Boss defeat branch outside ordinary actor-prefix scope'
 execute(cpu,[7,12]);checkpoint(0x1839);execute(cpu,[10,10,10]);count=0
 for n in range(8):
  execute(cpu,[7,4])
  if actors[n*48]:execute(cpu,[7,4]);count+=1
  else:cpu.execute(12)
  execute(cpu,[11,13 if n<7 else 8])
 execute(cpu,[4,4]);execute(cpu,[12] if count else [7,7]);cpu.execute(13);active=count or 128;checkpoint(0x1853)
 parts=full_actor_cost(rom,room,persistence)['components'];assert cpu.foreground_tstates==sum(parts[k] for k in ['clear_and_list','stats','persistence','boss_gate','count'])-24
 return dict(actor_points=points,persistence=persistence)

def predict_actor_prefix(rom,phase,ram,sound,room,hud_context,refresh,history,flags):
 prior=predict_history(rom,phase,ram,sound,room,hud_context,refresh,history,flags);end=prior['history_points'][-1]
 result=actor_prefix_work(rom,end['prediction'],room,end['flags'][room]);result['prior']=prior;return result
