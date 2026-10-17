"""Chain16D0..24B9 graphics load timing from one original entry snapshot."""
from foreground_phase import ForegroundPhase
from graphics_prefix_phase import predict_graphics_prefix
from ram_plane_loading_cost import ram_plane_cost
from class0_graphics_loading_cost import class0_graphics_cost

def execute(cpu,seq):
 for t in seq:cpu.execute(t)

def ldir(cpu,count):execute(cpu,[21]*(count-1)+[16])

def plane_decode(cpu,source,destination,planes):
 start=source;before=cpu.foreground_tstates;cpu.execute(4)
 for plane in range(planes):
  address=destination+plane;execute(cpu,[11,11])
  while True:
   command=cpu.rom[source];source+=1;execute(cpu,[7,4])
   if not command:cpu.execute(12);break
   execute(cpu,[7,10]);literal=bool(command&128);count=(command&127) or 256
   execute(cpu,[7,4] if literal else [4,6])
   for n in range(count):
    if literal:cpu.execute(6);source+=1
    execute(cpu,[7,7,4,4,4])
    execute(cpu,[12] if (address&255)+planes<256 else [7,4])
    address=(address+planes)&65535;cpu.execute(13 if n+1<count else 8)
   if not literal:source+=1
   execute(cpu,[6,12])
  execute(cpu,[10,10,6,6,13 if plane+1<planes else 8])
 cpu.execute(10);expected=ram_plane_cost(cpu.rom,start,destination,planes)
 assert cpu.foreground_tstates-before==expected['tstates'] and source==expected['source_end']
 return source

def predict_graphics_load(rom,phase,ram,sound,cpu_factory=ForegroundPhase,prefix_model=predict_graphics_prefix):
 prefix=prefix_model(rom,phase,ram,sound)
 cpu=cpu_factory(rom,prefix['phase'],prefix['ram'],prefix['sound']);points={0x1706:prefix}
 def checkpoint(pc):
  cpu.checkpoint();r=cpu.result();r['wall_master_cycles']+=prefix['wall_master_cycles'];r['foreground_tstates']+=prefix['foreground_tstates'];r['IRQ_tstates']+=prefix['IRQ_tstates']
  for k in ['foreground_M1','IRQ_M1']:
   if k in r:r[k]+=prefix[k]
  r['events']=prefix['events']+[dict(e,entry_offset_master=e['entry_offset_master']+prefix['wall_master_cycles']) for e in r['events']];points[pc]=r
 execute(cpu,[10,7,17]);plane_decode(cpu,prefix['source_end'],0xc900,2);checkpoint(0x170e)
 execute(cpu,[10,10,10]);ldir(cpu,8);execute(cpu,[10,7]);ldir(cpu,8);checkpoint(0x1720)
 execute(cpu,[17,13,4,5,13,4,7,10,10,10,11,11]);ldir(cpu,8);execute(cpu,[10,10,10]);ldir(cpu,8);cpu.execute(10)
 execute(cpu,[7,13,17,13,4,11,7,13,17])
 lookup=[11,4,4,12,7,6,7,4,10]
 execute(cpu,[10,13,4]+lookup+[10,7])
 table=int.from_bytes(rom[0x8259:0x825b],'little');n=0
 while rom[table+n]<128:
  execute(cpu,[7,6,4,10,11,11,4,7,11,11,11,10,11,10]);ldir(cpu,8);execute(cpu,[10,10,4,12]);n+=1
 execute(cpu,[7,6,4,10,10]);cpu.execute(8,'M1_2');cpu.execute(8,'M1_2') #Two SLA C at 81EC/81EE.
 for _ in range(n*4):execute(cpu,[4,5,7,7,7,7,6,6,6,12])
 execute(cpu,[4,11]);checkpoint(0x1733)
 execute(cpu,[13,4,10]+lookup+[7,13,10,7,17])
 terrain_pc=int.from_bytes(rom[0x1759:0x175b],'little')
 plane_decode(cpu,11*0x4000+(terrain_pc&0x3fff),0xd100,4);checkpoint(0x1748)
 cpu.execute(17);cpu.execute(4,'DI');execute(cpu,[13,7,13,10,10,10,10]);ldir(cpu,1024)
 execute(cpu,[10,13,7,13]);cpu.execute(4,'EI');cpu.execute(10);checkpoint(0x24b9)
 assert points[0x24b9]['foreground_tstates']==class0_graphics_cost(rom)['foreground_tstates']
 return points
