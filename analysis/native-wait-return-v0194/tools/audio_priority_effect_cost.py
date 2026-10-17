"""Original81F8 priority-effect queue and8211 restoration,valid effect indices."""
from audio_dispatch_cost import POINTER_COST,CHANNEL_COPY_COST

def priority_effect_cost(rom,state):
 r=bytearray(state);assert len(r)==400;de=0xde09;cost=10+7+7
 def read(a):return rom[0x18000+(a&0x3fff)]
 def finish():return dict(state=bytes(r),tstates=cost,de=de)
 def latch(command):
  r[0xe]=command;work=13+4+13+4+10
  if not r[0xf]&128:
   work+=10+(12 if r[0xf]==0 else 7+10)+7+6+7+7+11
   r[0x130 if r[0xf]==0 else 0x160]=r[0xf]
  return work+4+10
 request=r[9]
 if request==128:
  cost+=12+4+7+latch(0);r[9]=0;return finish()
 cost+=7+7
 if not request&127:cost+=11;return finish()
 if not 0x90<=request<=0xac:raise NotImplementedError(f'Priority queue request {request:02X}')
 cost+=5+14+14+17+4+10+4+7+11+7+19
 priority=read(0x8ad5+(request&127)-1)
 if priority<r[0x10]:cost+=12
 else:r[0x10]=priority&127;r[0xe]=request;cost+=7+7+19+7+19
 r[9]=0;de=0xde0a;cost+=4+7+6+10+19+17
 command=r[0xe]
 if not 0x90<=command<=0xac:raise NotImplementedError(f'Priority restoration command {command:02X}')
 cost+=latch(command)+7+10+17+POINTER_COST+6+6+7+6+7
 pointer=0x8b30+(command-0x90)*2;header=read(pointer)|(read(pointer+1)<<8)
 channel=read(header+2);header+=1
 if channel!=0xc0:
  cost+=7+10+14+7+4+10;de=0xdf60;background=0xd0;target=0x160
  if r[target]&128:r[0xf]=r[target];cost+=13+10;return finish()
  cost+=7+12;r[0xf]=1
 else:
  cost+=12+13+4+10
  if r[0x160]&128:
   cost+=7+7
   if not r[0x160]&64:r[0xf]=128;cost+=12+13+10;return finish()
   cost+=7
  cost+=10+14+7+4+10;de=0xdf30;background=0xa0;target=0x130
  if r[target]&128:r[0xf]=r[target];cost+=13+10;return finish()
  cost+=4;r[0xf]=0
 cost+=13+10+23+CHANNEL_COPY_COST
 r[background]|=4;r[target:target+9]=bytes(read(header+i) for i in range(9))
 r[target+9]=0x30;r[target+10]=1;r[target+0x27:target+0x2a]=bytes(3);de=0xde00+target+0x30
 return finish()
