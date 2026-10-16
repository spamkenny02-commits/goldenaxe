"""Original854B ADSR/table M1 counts,including indexed operations andunwinds."""
from audio_adsr_cost import adsr_cost
from audio_table_envelope_cost import table_envelope_cost
from audio_dispatch_refresh import POINTER_M1

def adsr_refresh(state,offset=0x40,de=0):
 output=adsr_cost(state,offset,de);mode=state[offset+7];count=3
 def finish():output['m1_fetches']=count;return output
 if not mode:count+=1;return finish()
 assert mode&128;count+=4;flags=state[offset+0x1d];value=state[offset+0x1f]
 if flags&16:
  count+=6;step=state[offset+0x20]
  if value>=step:count+=1;value-=step
  else:count+=2;value=0
  count+=3;count+=1 if value else 7
 else:
  count+=3
  if flags&32:
   count+=8;limit=state[offset+0x22];value+=state[offset+0x21]
   if value>255:count+=2;value=limit
   else:
    count+=2
    if value<limit:count+=1
    else:count+=2;value=limit
   count+=3
   if value!=limit:count+=1
   else:count+=5+(3 if flags&8 else 2)+3
  else:
   count+=3
   if flags&64:
    count+=6;value+=state[offset+0x23]
    if value<=255:count+=1
    else:count+=2;value=255
    count+=3;count+=1 if value!=255 else 7
   else:
    count+=6;value+=state[offset+0x24]
    if value<=255:count+=3
    else:
     count+=10+4
     count+=1 if state[offset]&4 else 6
     return finish()
 count+=8;return finish()

def table_envelope_refresh(rom,state,offset=0x40,de=0x8a0b):
 output=table_envelope_cost(rom,state,offset,de);r=bytearray(state);mode=r[offset+7];count=3
 def finish():output['m1_fetches']=count;return output
 def read(address):
  address&=65535
  if address<0x8000:return rom[address]
  if address<0xc000:return rom[0x18000+(address&0x3fff)]
  if 0xde00<=address<0xdf90:return r[address-0xde00]
  raise NotImplementedError(f'Uncaptured envelope RAM {address:04X}')
 if not mode:count+=1;return finish()
 assert mode<128;count+=5+POINTER_M1+1;pointer=0x897f+(mode-1)*2;table=read(pointer)|(read(pointer+1)<<8)
 for guard in range(256):
  value=read(table+r[offset+0x1f]);count+=11
  if value<128:count+=4;return finish()
  count+=2
  if value==0x82:
   count+=9+(1 if r[offset]&4 else 6);return finish()
  count+=2
  if value==0x81:count+=5;return finish()
  count+=2
  if value==0x80:count+=3;r[offset+0x1f]=0
  else:count+=4;de=(de+1)&65535;r[offset+0x1f]=read(de)
  count+=2
 raise ValueError('Envelope control loop does not terminate within256 steps')
