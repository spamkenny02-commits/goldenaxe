"""Original hero initialization instruction phases from its full RAM entry state."""
from hero_initialization_cost import hero_initialization_cost
from graphics_prefix_refresh import GraphicsPrefixRefreshPhase
from graphics_load_phase import execute,ldir

def predict_hero(rom,phase,ram,sound,refresh,cpu_class=GraphicsPrefixRefreshPhase):
 original=bytes(ram);mem=bytearray(ram);expected=hero_initialization_cost(rom,ram);final=expected['ram']
 compact=bytes(mem[:80]+mem[0x1d00:0x1e00])
 class ScopedPhase(cpu_class):entry_refresh=refresh
 cpu=ScopedPhase(rom,phase,compact,sound);points={}
 def checkpoint(pc):
  cpu.ram[0x41:0x50]=mem[0x41:0x50];cpu.checkpoint();points[pc]=dict(cpu.result(),hero_ram=bytes(mem))
 def ordinary(seq):
  for t in seq:cpu.execute(t,'M1_1' if t==16 else None)
 execute(cpu,[14,4]+[13]*5+[19]*4)
 for a in [0x312,0x310,0x304,0x30c,0x30b]:mem[a]=0
 mem[0x300:0x304]=bytes([2,0,240,3]);cpu.execute(17);checkpoint(0x369f)
 old,selected,direction=mem[0x41],mem[0xdf],mem[0x30a];execute(cpu,[13,7])
 if old==3:
  cpu.execute(12);ordinary([13,7,4,13,4,4,4,10,11,4,4,12,7,6,7,4,10,16,7,13,19,19,10])
 else:
  execute(cpu,[7,7,13,4]);c=0
  if selected==1:execute(cpu,[7,13,4,4]);c=(mem[0xe1]+1)&255
  else:cpu.execute(12)
  execute(cpu,[13,7])
  if old==2:cpu.execute(7);cpu.execute(8,'M1_2');c|=4
  else:cpu.execute(12)
  execute(cpu,[10,4,4,4,4,4,4]);execute(cpu,[7,4] if ((c*8)&255)+160>255 else [12]);ordinary([16,10,4,4,4,19,4,4,4,19,4,7,13,7])
  execute(cpu,[7,4,7,4] if old==5 else [12]);ordinary([11,11,7,6,7,4,16,7]);cpu.execute(8,'M1_2');execute(cpu,[7,4] if c&4 else [12]);execute(cpu,[13,10])
 for a in [0x42,0x43,0x44,0x308,0x309]:mem[a]=final[a]
 checkpoint(0x2c8a);execute(cpu,[17,10,10,10,10]);ldir(cpu,383);cpu.execute(10);mem[0x330:0x4b0]=bytes(384)
 execute(cpu,[13,4,4,4,13,4,4,4,4,13,4,4]);execute(cpu,[7,4] if mem[0xbf] else [12]);execute(cpu,[4,13]);mem[0x31a]=final[0x31a];checkpoint(0x2ca6)
 execute(cpu,[17,10,7,7,6,11,7,4,4,11,11,11,10,11,7,10,13]);mem[0x319]=final[0x319]
 x,y=mem[0x313],mem[0x311];execute(cpu,[13,4,13,4,4,7,4,4,4,4,4,7,4,4,4,4,4,4,7])
 if (x|y)&7:cpu.execute(7);cpu.execute(8,'M1_2')
 else:cpu.execute(12)
 execute(cpu,[4,13,10,17,19,4,7,4,7,11,11,11,19,4,4,4,7,4,4]);yy=(y-12)&248;xx=((x-12)&255)>>2&62;execute(cpu,[7,4] if ((yy*8)&255)+xx>255 else [12]);execute(cpu,[10,11,7,4,7,10,4,10,10]);address=0xd600+yy*8+xx
 for row in range(3):
  execute(cpu,[16]*8+[7,4,4]);mem[0x48+row*8:0x50+row*8]=original[address-0xc000:address-0xc000+8];address+=8
  execute(cpu,[7,4] if (address&255)+56>255 else [12]);address+=56;cpu.execute(13 if row<2 else 8)
 ordinary([10,11,16]);mem[0x60:0x62]=((address+0x29be)&65535).to_bytes(2,'little');mem[0x6b]=final[0x6b]
 execute(cpu,[13,4])
 if mem[0xec]:cpu.execute(12)
 else:
  execute(cpu,[7,10,10])
  for n in range(12):
   a=0x49+n*2;execute(cpu,[7,4])
   if mem[a]&32:cpu.execute(7);cpu.execute(15,'M1_2');mem[a]|=128
   else:cpu.execute(12)
   execute(cpu,[4,4,13 if n<11 else 8])
 execute(cpu,[13,7]);graphics=mem[0x40];terrain=0
 if graphics==1:execute(cpu,[12,4])
 else:
  cpu.execute(7);execute(cpu,[12,14] if graphics==0 else [7,14,12]);table=0x2544 if graphics==0 else 0x2569
  for i,any_match in enumerate([True,False,False,True,True]):
   record=rom[table+i*4:table+i*4+4];pointer=int.from_bytes(record[:2],'little');count=record[2] or 256;values=rom[pointer:pointer+count]
   def search(value):
    found=value in values;n=values.index(value)+1 if found else count;execute(cpu,[21]*(n-1)+[16]);return found
   execute(cpu,[17,10]);cpu.execute(15,'M1_2');execute(cpu,[13,19,19,19]);found=search(mem[0x52]);matched=False
   if any_match and found:execute(cpu,[12,19,10]);matched=True
   elif not any_match and not found:cpu.execute(11)
   else:
    execute(cpu,[7,12] if any_match else [5]);execute(cpu,[13,19,19,19]);found=search(mem[0x54]);execute(cpu,[5,19,10] if found else [11]);matched=found
   cpu.execute(12 if matched else 7)
   if matched:terrain=record[3];break
  else:cpu.execute(4)
 checkpoint(0x2d3e);cpu.execute(13);mem[0x41]=terrain;execute(cpu,[13,4])
 if not mem[0xf0]:cpu.execute(12)
 else:
  execute(cpu,[7,13,10,7,7]);cpu.execute(8,'M1_2');flags=mem[0x53]&mem[0x55]&192
  if not flags&64:cpu.execute(12)
  else:
   execute(cpu,[7,4,7 if flags&128 else 12,10,7])
   for n in range(12):
    a=0x49+n*2;cpu.execute(12,'M1_2')
    if mem[a]&64:
     cpu.execute(7);cpu.execute(15,'M1_2');mem[a]&=127
     if flags&128:cpu.execute(12)
    else:
     cpu.execute(12)
     if flags&128:cpu.execute(15,'M1_2');mem[a]|=128
    execute(cpu,[6,6,13 if n<11 else 8])
   if flags&128:cpu.execute(12)
 cpu.execute(10);checkpoint(0x24e7)
 assert cpu.foreground_tstates==expected['foreground_tstates']
 assert all(mem[i]==final[i] for i in list(range(0x41,0x6c))+list(range(0x300,0x4b0)))
 return points
