"""Predict original0B95 wait from entry raster/latches and bounded RAM/audio state."""
from audio_reader_cost import reader_cost
from audio_irq_wrapper_cost import audio_irq_wrapper_cost
from full_irq_cost import full_irq_cost
from irq_raster_phase import predict_palette_wait
from audio_reader_refresh import reader_refresh
from audio_irq_wrapper_refresh import audio_irq_wrapper_refresh
from full_irq_refresh import full_irq_refresh
from source_rng_refresh import advance_refresh

def predict_save_wait(rom,phase,ram,sound,refresh=None):
 r=bytearray(ram);audio=bytes(sound);assert len(r)==336 and len(audio)==400
 cpu,line,base,lines,overflow,interlaced,reg1,hardware,iff,afterei,pending,reg0=phase
 assert (lines,overflow) in [(262,0xda),(313,0xf2)] and hardware in [0x20,0x21]
 assert not interlaced and not reg1&4 and reg1&0x20 and not reg0&0x10
 delta=((cpu-base+0x80000000)&0xffffffff)-0x80000000;time=line*3420+delta;started=time;period=lines*3420
 next_vint=193*3420+((time-193*3420)//period+1)*period;enabled=bool(iff);blocked=bool(afterei);pending=bool(pending);a=0;events=[];irq_tstates=0;first_instruction=True
 foreground_M1=irq_M1=0
 def boundary():
  nonlocal time,next_vint,pending,enabled,blocked,audio,r,irq_tstates,refresh,irq_M1
  while time>=next_vint:pending=True;next_vint+=period
  if pending and enabled and not blocked:
   accepted=time;driver=reader_cost(rom,audio,de=0)
   if refresh is not None:
    m1_driver=reader_refresh(rom,audio,de=0);assert (m1_driver['state'],m1_driver['tstates'],m1_driver['de'])==(driver['state'],driver['tstates'],driver['de'])
   if r[0x2e]:
    enter=time+72*15;vline=(enter//3420)%lines;entry_phase=(enter%3420,vline,0,lines,overflow,0,reg1,hardware)
    preamble=full_irq_cost(rom,r,0,0 if r[0x33] else 1,0,16,audio[3],0)
    palette=predict_palette_wait(entry_phase,sum(list(preamble['stages'].values())[:4]),r[0x33],audio[3])
    full=full_irq_cost(rom,r,palette['taken'],palette['exits'],0,16,audio[3],driver['tstates']);cost=full['whole_IRQ_tstates']
    if refresh is not None:fetches=full_irq_refresh(rom,r,palette['taken'],palette['exits'],0,16,audio[3],driver['tstates'],m1_driver['m1_fetches'])['whole_IRQ_M1']
    r=bytearray(full['state']);kind='full'
   else:
    wrapper=audio_irq_wrapper_cost(r[0x30]!=0);cost=wrapper['interrupt_accept_and_vector']+wrapper['to_return_excluding_reader']+driver['tstates']+wrapper['return_instruction']
    if refresh is not None:fetches=audio_irq_wrapper_refresh(r[0x30]!=0)['whole_IRQ_excluding_reader_M1']+m1_driver['m1_fetches']
    if r[0x30]:r[0x30]-=1
    kind='audio'
   audio=driver['state'];time+=cost*15;irq_tstates+=cost;pending=False;enabled=True;blocked=False
   if refresh is not None:refresh=advance_refresh(refresh,fetches);irq_M1+=fetches
   assert time<next_vint,'Nested/new VINT during handler not supported'
   events.append(dict(kind=kind,entry_offset_master=accepted+72*15-started,tstates=cost))
 def execute(ticks,effect=None,fetches=1):
  nonlocal time,blocked,enabled,a,first_instruction,refresh,foreground_M1
  #Capture is at instruction entry after GPG has already checked IRQ/EI.
  first=first_instruction
  if first_instruction:first_instruction=False
  else:boundary()
  if refresh is not None:refresh=advance_refresh(refresh,fetches-int(first));foreground_M1+=fetches
  blocked=False;time+=ticks*15
  if effect=='load_one':a=1
  elif effect=='gate':r[0x2e]=a
  elif effect=='enable':enabled=True;blocked=True
  elif effect=='load_gate':a=r[0x2e]
 prefix=[11]*4+[4,4]+[11]*4+[15,15,13,11,7,13,4]
 for i,ticks in enumerate(prefix):execute(ticks,{14:'load_one',15:'gate',16:'enable'}.get(i),2 if i in [10,11] else 1) #PUSH IX/IY;other saves are ordinary.
 taken=0
 for guard in range(8192):
  execute(13,'load_gate');execute(4)
  if a:execute(12);taken+=1
  else:execute(7);boundary();break
 else:raise ValueError('Wait loop exceeds frame-scale bound')
 foreground=174+taken*29+24;assert time-started==(foreground+irq_tstates)*15
 result=dict(taken=taken,exits=1,foreground_tstates=foreground,IRQ_tstates=irq_tstates,wall_master_cycles=time-started,events=events,gate=r[0x2e],clock=r[0x2f],phase=(time%3420,(time//3420)%lines,0,lines,overflow,0,reg1,hardware,int(enabled),int(blocked),int(pending),reg0),ram=bytes(r),sound=audio)
 if refresh is not None:result.update(refresh=advance_refresh(refresh,1),foreground_M1=foreground_M1,IRQ_M1=irq_M1)
 return result
