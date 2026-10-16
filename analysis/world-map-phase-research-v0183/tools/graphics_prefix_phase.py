"""Instruction timing for changed class0 graphics:16D0..1706 (patterns)."""
from foreground_phase import ForegroundPhase
from reveal_phase_prediction import rst28
from actor_loading_cost import rle_cost
from class0_graphics_loading_cost import class0_graphics_cost

def pattern_rle(cpu,source,destination):
 start=source;before=cpu.foreground_tstates
 for t in [7,4]:cpu.execute(t)
 for plane in range(4):
  dst=destination+plane
  for t in [11,11]:cpu.execute(t)
  while True:
   command=cpu.rom[source];source+=1
   for t in [7,6,4]:cpu.execute(t)
   if not command:cpu.execute(12);break
   for t in [7,4,8,4,4]:cpu.execute(t)
   literal=bool(command&128);count=(command&127) or 256
   for n in range(count):
    rst28(cpu)
    for t in [7,11,4,7 if literal else 12]:cpu.execute(t)
    if literal:cpu.execute(6);source+=1
    for t in [4,4,4,4]:cpu.execute(t)
    if (dst&255)+4<256:cpu.execute(12)
    else:cpu.execute(7);cpu.execute(4)
    dst=(dst+4)&65535;cpu.execute(13 if n+1<count else 8)
   cpu.execute(4)
   if literal:cpu.execute(12)
   else:
    for t in [7,6,12]:cpu.execute(t)
    source+=1
  cpu.execute(20);cpu.ram[0x31:0x33]=dst.to_bytes(2,'little')
  for t in [10,6,10,13 if plane<3 else 8]:cpu.execute(t)
 for t in [20,6,4,4,4]:cpu.execute(t)
 if ((dst+1)&255)>=4:cpu.execute(12)
 else:cpu.execute(7);cpu.execute(4)
 cpu.execute(10)
 expected=rle_cost(cpu.rom,start,destination)
 assert cpu.foreground_tstates-before==expected['tstates'] and source==expected['source_end']
 return source

def predict_graphics_prefix(rom,phase,ram,sound):
 cpu=ForegroundPhase(rom,phase,ram,sound)
 assert not ram[0x11]&64
 #175F class0 ordinary world room. Room class/bank-change are scoped inputs.
 for t in [17,13,4,7,7,13,7,7,7,13,7,7,7,7,4,13]:cpu.execute(t)
 cpu.ram[0x40]=0;cpu.execute(10)
 for t in [10,7,7,10,7,7,5,7,13,13]:cpu.execute(t)
 updated=bytearray(cpu.sound);updated[6]=0xb0;cpu.sound=bytes(updated)
 for t in [13,7,10,13,13,10,10,10]+[21]*15+[16,10,17]:cpu.execute(t)
 source=pattern_rle(cpu,0x3c010,0x4000);cpu.checkpoint()
 parts=class0_graphics_cost(rom)['components']
 assert cpu.foreground_tstates==parts['classify_and_bank_change']+parts['palette_and_patterns']
 result=cpu.result();result['source_end']=source
 return result
