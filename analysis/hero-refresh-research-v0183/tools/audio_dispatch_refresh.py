"""Original80FF M1 counts from semantic branches; shared helper counts explicit."""
from audio_dispatch_cost import dispatch_cost
from audio_prefix_refresh import stop_refresh

POINTER_M1=9 #8424: ordinary instructions only.
CHANNEL_COPY_M1=40 #81CA includes nine ED-prefixed LDI and indexed writes.

def dispatch_refresh(rom,state):
 output=dispatch_cost(rom,state);r=bytearray(state);command=r[5];count=4
 def read(address):return rom[0x18000+address-0x8000]
 def pointer(address):return read(address)|(read(address+1)<<8)
 def finish():output['m1_fetches']=count;return output
 stop=stop_refresh(state)['m1_fetches']
 if not command&128:count+=stop;return finish()
 count+=1
 if command<0x90:
  count+=2
  if command==0x80:count+=1;return finish()
  assert command<=0x8d
  count+=3+stop+12+2+POINTER_M1+3
  header=pointer(0x8b16+(command-0x81)*2);channels=read(header)
  count+=channels*(1+CHANNEL_COPY_M1+1)+3
  return finish()
 count+=2
 if command<0xad:
  count+=5+POINTER_M1+2;header=pointer(0x8b30+(command-0x90)*2);channels=read(header);header+=1
  for _ in range(channels):
   channel=read(header+1);count+=4
   if channel==0xa0:count+=4;offset,background=0x100,0x70
   else:
    count+=2
    if channel==0xc0:
     count+=5
     if r[0x160]&64:count+=1
     else:count+=5;r[0x160]|=4
     count+=4;offset,background=0x130,0xa0
    else:count+=5;offset,background=0x160,0xd0
   count+=1+2+CHANNEL_COPY_M1+1
   r[background]|=4;r[offset:offset+9]=bytes(read(header+n) for n in range(9));header+=9
  count+=4;return finish()
 count+=3
 if command>=0xb5:count+=stop;return finish()
 assert command in [0xb0,0xb1,0xb2,0xb3]
 count+=3+POINTER_M1+1
 if command==0xb0:count+=9
 elif command==0xb1:count+=stop
 elif command==0xb2:count+=5+3*7+1
 else:
  count+=7
  if not r[0xf]&128:count+=7 if not r[0xf] else 8
  count+=6
 return finish()
