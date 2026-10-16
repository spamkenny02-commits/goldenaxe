"""Chain scripts,music and reveal through0ACE from the single16D0 input."""
from loader_hero_refresh_phase import predict_loader_hero
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_load_phase import execute
from world_load_tail_cost import room_script_setup_cost,world_music_setup_cost
from reveal_phase_prediction import clear_prefix,prepare_prefix,restore_and_enable
from wait_raster_prediction import predict_save_wait

def predict_loader_tail(rom,phase,initial,sound,refresh):
 prior=predict_loader_hero(rom,phase,initial,sound,refresh);base=prior['hero_points'][0x24e7];mem=bytearray(base['hero_ram']);room=int.from_bytes(mem[0xb9:0xbb],'little');points=[]
 def new_cpu(base):
  class ScopedPhase(GraphicsPrefixRefreshPhase):entry_refresh=base['refresh']
  return ScopedPhase(rom,base['phase'],base['ram'],base['sound'])
 cpu=new_cpu(base)
 def combine(p):
  p=dict(p)
  for k in ['wall_master_cycles','foreground_tstates','IRQ_tstates','foreground_M1','IRQ_M1']:p[k]+=base[k]
  p['events']=base['events']+[dict(e,entry_offset_master=e['entry_offset_master']+base['wall_master_cycles']) for e in p['events']];return p
 def record(pc,p=None):
  if p is None:cpu.checkpoint();p=cpu.result()
  points.append(dict(pc=pc,prediction=combine(p),script_ram=bytes(mem)))
 cpu.execute(17);record(0x5b20);before=cpu.foreground_tstates
 for t in [10,16,16,16,20,20,13,13,7,13,16,11,10,11,7,6,7,20,13,4]:cpu.execute(t,'M1_1' if t==16 else None)
 for a in [0x1ce0,0x1ce2,0x1ce4]:mem[a:a+2]=b'\xb0\xc0'
 mem[0x62:0x64]=mem[0x60:0x62];mem[0x64]=mem[0x30a];mem[0xa4:0xa6]=rom[0xb762+room*2:0xb764+room*2]
 if mem[0xa2]&128:execute(cpu,[7,7,13]);mem[0xa8]=2
 else:cpu.execute(12)
 cpu.execute(10);assert cpu.foreground_tstates-before==room_script_setup_cost(mem[0xa2]);cpu.execute(17);record(0x1caf);before=cpu.foreground_tstates
 execute(cpu,[13,7,7,7,10,10,13]);table=rom[0x1d02:0x1d0d];found=room in table;n=table.index(room)+1 if found else 11;execute(cpu,[21]*(n-1)+[16]);cpu.execute(7)
 execute(cpu,[7,7,12] if found else [12]);command=132 if found else 130;record(0x1cf8);execute(cpu,[10,7,7]);previous=mem[0x65];mem[0x65]=command
 if command==previous:cpu.execute(11)
 else:
  execute(cpu,[5,13]);audio=bytearray(cpu.sound);audio[6]=command;cpu.sound=bytes(audio);cpu.execute(10)
 assert cpu.foreground_tstates-before==world_music_setup_cost(rom,room,previous)['foreground_tstates'];record(0x24ed);execute(cpu,[7,13]);cpu.ram[0x1d]=12;mem[0x1d]=12;execute(cpu,[10,10]);record(0x1fa7)
 clear_prefix(cpu);record(0xaa4,cpu.result());prepare_prefix(cpu);record(0xb95,cpu.result())
 wait=predict_save_wait(rom,cpu.phase(),cpu.ram,cpu.sound,cpu.refresh);base=points[-1]['prediction'];record(0xbb3,wait);base=points[-1]['prediction'];cpu=new_cpu(base)
 restored=restore_and_enable(cpu);record(0xac0,restored);record(0xace,cpu.result())
 return dict(prior=prior,tail_points=points,command=command,script_ram=bytes(mem))
