"""Compute recent-room decisions and original RNG from the single loader entry."""
from map_hud_phase import predict_map_hud
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_load_phase import execute,ldir
from source_rng_reference import source_rng

def predict_history(rom,phase,ram,sound,room,hud_context,refresh,history,flags):
 points=predict_map_hud(rom,phase,ram,sound,room,hud_context,refresh);base=points[0x24bf]
 class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=base['refresh']
 cpu=ScopedPhase(rom,base['phase'],base['ram'],base['sound']);history=bytearray(history);flags=bytearray(flags)
 assert room<256 and len(history)==16 and len(flags)==256
 observations=[];draws=[]
 def checkpoint(pc,expected_A=None,expected_HL=None):
  cpu.checkpoint();p=cpu.result()
  for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:p[k]+=base[k]
  p['events']=base['events']+[dict(e,entry_offset_master=e['entry_offset_master']+base['wall_master_cycles']) for e in p['events']]
  observations.append(dict(pc=pc,prediction=p,history=bytes(history),flags=bytes(flags),expected_A=expected_A,expected_HL=expected_HL))
 def cpir(value):
  count=history.index(value)+1 if value in history else 16
  execute(cpu,[21]*(count-1)+[16]);return value in history
 def random():
  checkpoint(0x4e1);seed=int.from_bytes(cpu.ram[0x28:0x2a],'little');transition=source_rng(seed,0)
  cpu.execute(16,'M1_1');execute(cpu,[4]*12);cpu.execute(15,'M1_2');cpu.execute(7 if transition['zero_seed_replaced'] else 12)
  if transition['zero_seed_replaced']:cpu.execute(10)
  checkpoint(0x4f7,expected_HL=transition['seed']);cpu.execute(9,'M1_2');value=source_rng(seed,cpu.refresh)['value'];cpu.execute(4);cpu.execute(16,'M1_1');cpu.ram[0x28:0x2a]=transition['seed'].to_bytes(2,'little');checkpoint(0x4fd,expected_A=value,expected_HL=transition['seed']);cpu.execute(10)
  draws.append(dict(seed=seed,next_seed=transition['seed'],value=value));return value
 cpu.execute(17);checkpoint(0x24c5)
 execute(cpu,[10,10,10,7]);ldir(cpu,31);execute(cpu,[10,10,10,10]);ldir(cpu,335)
 cpu.execute(17);execute(cpu,[13,4,7,7])
 for attempt in range(3):
  execute(cpu,[11,17,13,10,10]);found=cpir(room)
  if found:cpu.execute(12)
  else:
   execute(cpu,[7,10,10,10]);ldir(cpu,15);cpu.execute(13);history[1:]=history[:-1];history[0]=room
  checkpoint(0x1c40);cpu.execute(17);value=random();execute(cpu,[10,10]);found=cpir(value);draws[-1].update(history_match=found,persistence_before=flags[value])
  if found:cpu.execute(11)
  else:
   execute(cpu,[5,12,4,7,7,4])
   if flags[value]:cpu.execute(11)
   else:execute(cpu,[5,10]);flags[value]=255;cpu.execute(10)
  execute(cpu,[10,13 if attempt<2 else 8])
 cpu.execute(10);cpu.execute(17);checkpoint(0x1780)
 return dict(loader_points=points,history_points=observations,draws=draws)
