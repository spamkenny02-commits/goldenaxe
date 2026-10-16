"""Original8000 state/cost/M1 composition with supported-command bounds retained."""
from audio_prefix_refresh import arbitration_refresh,tempo_refresh,fade_refresh
from audio_dispatch_refresh import dispatch_refresh
from audio_priority_effect_refresh import priority_effect_refresh
from audio_tone_channel_refresh import tone_channel_refresh
from audio_noise_channel_refresh import noise_channel_refresh

def reader_refresh(rom,state,de=0):
 r=bytearray(state);cost=10+7+4;m1=3
 def result():return dict(state=bytes(r),tstates=cost,de=de,m1_fetches=m1)
 if r[0xa]:
  cost+=7;m1+=1
  if not r[0xa]&128:cost+=11;m1+=1;return result()
  r[0xa]=(r[0xa]-1)&255;r[5]=128
  cost+=5+11+10+22+10+7+7+(9*21+16)+20+10+7+13+10
  #22T=two PUSHes,20T=two POPs;OTIR ten iterations each fetch ED+opcode.
  m1+=1+1+1+2+1+1+1+20+2+1+1+1+1
  return result()
 cost+=12;m1+=1
 for function,args in [(arbitration_refresh,(rom,)),(tempo_refresh,()),(fade_refresh,()),(dispatch_refresh,(rom,)),(priority_effect_refresh,(rom,))]:
  output=function(*args,r);r=bytearray(output['state']);cost+=17+output['tstates'];m1+=1+output['m1_fetches']
  if 'de' in output:de=output['de']
 cost+=13+4+10;m1+=3
 if r[3]:
  cost+=13+4+7;m1+=3;phase=(r[4]+1)&255
  if phase<6:cost+=12;m1+=1
  else:cost+=7+4;m1+=2;phase=0
  r[4]=phase;cost+=4+13;m1+=2
  if not phase:cost+=11;m1+=1;return result()
  cost+=5;m1+=1
 for offset in [0x40,0x70,0xa0,0xd0,0x100,0x130,0x160]:
  cost+=14+20;m1+=4
  if not r[offset]&128:cost+=10;m1+=1;continue
  cost+=17;m1+=1
  output=noise_channel_refresh(rom,r,offset,de) if offset==0xd0 else tone_channel_refresh(rom,r,offset,de)
  r=bytearray(output['state']);cost+=output['tstates'];m1+=output['m1_fetches'];de=output['de']
 cost+=10;m1+=1
 return result()
