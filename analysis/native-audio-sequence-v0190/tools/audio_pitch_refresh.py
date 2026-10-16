"""Original82C5 M1 count for delay/vibrato/table paths andcaller unwinds."""
from audio_pitch_cost import pitch_cost
from audio_dispatch_refresh import POINTER_M1
from audio_source_memory import read_audio_byte

def pitch_refresh(rom,state,offset=0x40,return_address=0x8507,de=None):
 output=pitch_cost(rom,state,offset,return_address,de);r=bytearray(state);mode=r[offset+6];count=7
 def finish():output['m1_fetches']=count;return output
 def read(a):return read_audio_byte(rom,r,a)
 if not mode:count+=1;return finish()
 count+=2
 if mode&128:
  count+=2
  if (r[offset+0x14]-1)&255:count+=1;return finish()
  count+=17
  count+=1 if (r[offset+0x15]-1)&255 else 18
  count+=4
  if (r[offset+0x17]-1)&255:count+=1;return finish()
  count+=12;return finish()
 count+=4+POINTER_M1+1;p=0x8a52+(mode-1)*2;table=read(p)|(read(p+1)<<8);base=int.from_bytes(r[offset+11:offset+13],'little')
 for guard in range(256):
  value=read(table+r[offset+0x15]);count+=11
  if value<128:count+=7;return finish()
  count+=2
  if value==0x83:count+=6;base=(base+1)&65535;r[offset+0x15]=read(base);continue
  count+=1
  if value>0x83:count+=8;return finish()
  count+=2
  if value==0x80:count+=5;r[offset+0x15]=0;continue
  count+=5;return finish()
 raise ValueError('Pitch control loop did not terminate')
