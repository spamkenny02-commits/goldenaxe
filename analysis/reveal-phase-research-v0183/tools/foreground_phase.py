"""Instruction timing scheduler for foreground with the source fullIRQ gate clear."""
from audio_reader_cost import reader_cost
from audio_irq_wrapper_cost import audio_irq_wrapper_cost

class ForegroundPhase:
 def __init__(self,rom,phase,ram,sound):
  cpu,line,base,self.lines,self.overflow,interlace,self.reg1,self.hardware,iff,blocked,pending,self.reg0=phase
  assert (self.lines,self.overflow) in [(262,0xda),(313,0xf2)] and not interlace and self.hardware in [0x20,0x21]
  assert self.reg1&0x20 and not self.reg0&0x10
  self.time=line*3420+((cpu-base+0x80000000)&0xffffffff)-0x80000000;self.started=self.time;self.period=self.lines*3420
  self.deadline=193*3420+((self.time-193*3420)//self.period+1)*self.period
  self.rom=rom;self.ram=bytearray(ram);self.sound=bytes(sound);assert len(ram)==336 and len(sound)==400 and not ram[0x2e]
  self.iff=bool(iff);self.blocked=bool(blocked);self.pending=bool(pending);self.first=True;self.IRQ_tstates=0;self.foreground_tstates=0;self.events=[];self.status_suppressions=0;self.vector_coalescences=0
 def boundary(self):
  for guard in range(64):
   while self.time>=self.deadline:self.pending=True;self.deadline+=self.period
   if not (self.pending and self.iff and not self.blocked):return
   assert not self.ram[0x2e];entered=self.time+72*15;driver=reader_cost(self.rom,self.sound,de=0);wrapper=audio_irq_wrapper_cost(self.ram[0x30]!=0)
   ticks=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+driver['tstates']+wrapper['return_instruction']
   #The vector reads status after interrupt13T,PUSH AF11T andIN11T.
   #A VINT reached before that read is cleared by the same acknowledgement.
   ack=self.time+35*15
   while ack>=self.deadline:self.deadline+=self.period;self.vector_coalescences+=1
   self.sound=driver['state'];self.time+=ticks*15;self.IRQ_tstates+=ticks
   if self.ram[0x30]:self.ram[0x30]-=1
   self.pending=False;self.iff=True;self.blocked=False;self.events.append(dict(kind='audio',entry_offset_master=entered-self.started,tstates=ticks))
  raise ValueError('Foreground audio IRQ catch-up exceeds bound')
 def execute(self,ticks,effect=None):
  if self.first:self.first=False
  else:self.boundary()
  self.blocked=False;self.time+=ticks*15;self.foreground_tstates+=ticks
  if effect=='DI':self.iff=False
  elif effect=='EI':self.iff=True;self.blocked=True
  elif effect=='status':
   self.pending=False
   #GPG suppresses VINT when the status read crosses line192->193.
   while self.time>=self.deadline:self.deadline+=self.period;self.status_suppressions+=1
 def reg1_write(self,value):
  assert value&0x20 and not value&4
  self.reg1=value
 def reg0_write(self,value):
  assert not value&0x10
  self.reg0=value
 def checkpoint(self):
  self.boundary();self.blocked=False;self.first=True
 def phase(self):
  return (self.time%3420,(self.time//3420)%self.lines,0,self.lines,self.overflow,0,self.reg1,self.hardware,int(self.iff),int(self.blocked),int(self.pending),self.reg0)
 def result(self):
  return dict(phase=self.phase(),ram=bytes(self.ram),sound=self.sound,wall_master_cycles=self.time-self.started,foreground_tstates=self.foreground_tstates,IRQ_tstates=self.IRQ_tstates,events=list(self.events),status_suppressions=self.status_suppressions,vector_coalescences=self.vector_coalescences)
