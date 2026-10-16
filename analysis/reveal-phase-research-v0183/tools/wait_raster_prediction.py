"""Predict original0B95 wait from entry raster/latches and bounded RAM/audio state."""
from audio_reader_cost import reader_cost
from audio_irq_wrapper_cost import audio_irq_wrapper_cost
from full_irq_cost import full_irq_cost
from irq_raster_phase import predict_palette_wait

def predict_save_wait(rom,phase,ram,sound):
 r=bytearray(ram);audio=bytes(sound);assert len(r)==336 and len(audio)==400
 cpu,line,base,lines,overflow,interlaced,reg1,hardware,iff,afterei,pending,reg0=phase
 assert (lines,overflow) in [(262,0xda),(313,0xf2)] and hardware in [0x20,0x21]
 assert not interlaced and not reg1&4 and reg1&0x20 and not reg0&0x10
 delta=((cpu-base+0x80000000)&0xffffffff)-0x80000000;time=line*3420+delta;started=time;period=lines*3420
 next_vint=193*3420+((time-193*3420)//period+1)*period;enabled=bool(iff);blocked=bool(afterei);pending=bool(pending);a=0;events=[];irq_tstates=0;first_instruction=True
 def boundary():
  nonlocal time,next_vint,pending,enabled,blocked,audio,r,irq_tstates
  while time>=next_vint:pending=True;next_vint+=period
  if pending and enabled and not blocked:
   accepted=time;driver=reader_cost(rom,audio,de=0)
   if r[0x2e]:
    enter=time+72*15;vline=(enter//3420)%lines;entry_phase=(enter%3420,vline,0,lines,overflow,0,reg1,hardware)
    preamble=full_irq_cost(rom,r,0,0 if r[0x33] else 1,0,16,audio[3],0)
    palette=predict_palette_wait(entry_phase,sum(list(preamble['stages'].values())[:4]),r[0x33],audio[3])
    full=full_irq_cost(rom,r,palette['taken'],palette['exits'],0,16,audio[3],driver['tstates']);cost=full['whole_IRQ_tstates'];r=bytearray(full['state']);kind='full'
   else:
    wrapper=audio_irq_wrapper_cost(r[0x30]!=0);cost=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+driver['tstates']+wrapper['return_instruction']
    if r[0x30]:r[0x30]-=1
    kind='audio'
   audio=driver['state'];time+=cost*15;irq_tstates+=cost;pending=False;enabled=True;blocked=False
   assert time<next_vint,'Nested/new VINT during handler not supported'
   events.append(dict(kind=kind,entry_offset_master=accepted+72*15-started,tstates=cost))
 def execute(ticks,effect=None):
  nonlocal time,blocked,enabled,a,first_instruction
  #Capture is at instruction entry after GPG has already checked IRQ/EI.
  if first_instruction:first_instruction=False
  else:boundary()
  blocked=False;time+=ticks*15
  if effect=='load_one':a=1
  elif effect=='gate':r[0x2e]=a
  elif effect=='enable':enabled=True;blocked=True
  elif effect=='load_gate':a=r[0x2e]
 prefix=[11]*4+[4,4]+[11]*4+[15,15,13,11,7,13,4]
 for i,ticks in enumerate(prefix):execute(ticks,{14:'load_one',15:'gate',16:'enable'}.get(i))
 taken=0
 for guard in range(8192):
  execute(13,'load_gate');execute(4)
  if a:execute(12);taken+=1
  else:execute(7);boundary();break
 else:raise ValueError('Wait loop exceeds frame-scale bound')
 foreground=174+taken*29+24;assert time-started==(foreground+irq_tstates)*15
 return dict(taken=taken,exits=1,foreground_tstates=foreground,IRQ_tstates=irq_tstates,wall_master_cycles=time-started,events=events,gate=r[0x2e],clock=r[0x2f],phase=(time%3420,(time//3420)%lines,0,lines,overflow,0,reg1,hardware,int(enabled),int(blocked),int(pending),reg0),ram=bytes(r),sound=audio)
