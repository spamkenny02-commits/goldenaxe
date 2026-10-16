"""Original8000 reader composition with explicit supported-command boundaries."""
from audio_arbitration_cost import arbitration_cost
from audio_prefix_cost import tempo_cost,fade_cost
from audio_dispatch_cost import dispatch_cost
from audio_priority_effect_cost import priority_effect_cost
from audio_tone_channel_cost import tone_channel_cost
from audio_noise_channel_cost import noise_channel_cost

def reader_cost(rom,state,de=0):
 r=bytearray(state);cost=10+7+4
 def result():return dict(state=bytes(r),tstates=cost,de=de)
 if r[0xa]:
  cost+=7
  if not r[0xa]&128:cost+=11;return result()
  r[0xa]=(r[0xa]-1)&255;r[5]=128
  cost+=5+11+10+22+10+7+7+(9*21+16)+20+10+7+13+10
  return result()
 cost+=12
 for function,args in [(arbitration_cost,(rom,)),(tempo_cost,()),(fade_cost,()),(dispatch_cost,(rom,)),(priority_effect_cost,(rom,))]:
  output=function(*args,r);r=bytearray(output['state']);cost+=17+output['tstates']
  if 'de' in output:de=output['de']
 cost+=13+4+10
 if r[3]:
  cost+=13+4+7;phase=(r[4]+1)&255
  if phase<6:cost+=12
  else:cost+=7+4;phase=0
  r[4]=phase;cost+=4+13
  if not phase:cost+=11;return result()
  cost+=5
 for offset in [0x40,0x70,0xa0,0xd0,0x100,0x130,0x160]:
  cost+=14+20
  if not r[offset]&128:cost+=10;continue
  cost+=17
  output=noise_channel_cost(rom,r,offset,de) if offset==0xd0 else tone_channel_cost(rom,r,offset,de)
  r=bytearray(output['state']);cost+=output['tstates'];de=output['de']
 cost+=10
 return result()
