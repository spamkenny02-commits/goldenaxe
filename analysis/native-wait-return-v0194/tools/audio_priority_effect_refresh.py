"""Original81F8 queue/restoration M1 count with explicit indexed instruction fetches."""
from audio_priority_effect_cost import priority_effect_cost
from audio_dispatch_refresh import POINTER_M1,CHANNEL_COPY_M1

def priority_effect_refresh(rom,state):
 output=priority_effect_cost(rom,state);r=bytearray(state);request=r[9];count=3
 def read(a):return rom[0x18000+(a&0x3fff)]
 def finish():output['m1_fetches']=count;return output
 def latch(command):
  work=7;r[0xe]=command
  if not r[0xf]&128:
   work+=7 if not r[0xf] else 8;r[0x130 if not r[0xf] else 0x160]=r[0xf]
  return work
 if request==128:count+=3+latch(0);return finish()
 count+=2
 if not request&127:count+=1;return finish()
 assert 0x90<=request<=0xac
 count+=14;priority=read(0x8ad5+(request&127)-1)
 if priority<r[0x10]:count+=1
 else:count+=7;r[0xe]=request
 count+=7;command=r[0xe];count+=latch(command)+3+POINTER_M1+5
 pointer=0x8b30+(command-0x90)*2;header=read(pointer)|(read(pointer+1)<<8);channel=read(header+2)
 if channel!=0xc0:
  count+=7
  if r[0x160]&128:count+=2;return finish()
  count+=2
 else:
  count+=4
  if r[0x160]&128:
   count+=2
   if not r[0x160]&64:count+=3;return finish()
   count+=1
  count+=6
  if r[0x130]&128:count+=2;return finish()
  count+=1
 count+=4+CHANNEL_COPY_M1
 return finish()
