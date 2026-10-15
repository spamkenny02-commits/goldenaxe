"""Original864F noise channel: held envelopes, note boundaries and F6/F7 controls."""
from audio_noise_note_cost import noise_note_cost
from audio_adsr_cost import adsr_cost
from audio_table_envelope_cost import table_envelope_cost

def noise_channel_cost(rom,state,offset=0xd0,de=0x8a0b):
 r=bytearray(state);assert len(r)==400
 def read(a):
  a&=65535
  if a<0x8000:return rom[a]
  if a<0xc000:return rom[0x18000+(a&0x3fff)]
  if 0xde00<=a<0xdf90:return r[a-0xde00]
  raise NotImplementedError(f'Uncaptured noise RAM {a:04X}')
 def result():return dict(state=bytes(r),tstates=cost,unwind=False)
 r[offset+10]=(r[offset+10]-1)&255;cost=23+10
 if r[offset+10]:
  cost+=17
  envelope=adsr_cost(r,offset) if r[offset+7]&128 else table_envelope_cost(rom,r,offset,de)
  r=bytearray(envelope['state']);cost+=envelope['tstates']
  if envelope.get('unwind',False):return result()
  cost+=20
  if r[offset]&4:cost+=11;return result()
  cost+=5+20
  if r[offset]&16:cost+=11;return result()
  volume=(envelope['accumulator']+r[offset+8])&255;cost+=5+19+8
  cost+=7+7 if volume&16 else 12
  cost+=19+7+11+10
  return result()
 r[offset]&=~16;cost+=23+19+19
 cursor=int.from_bytes(r[offset+3:offset+5],'little')
 for guard in range(256):
  note=read(cursor);cursor=(cursor+1)&65535;cost+=7+6+7
  if note<0xe0:break
  if note not in [0xf6,0xf7]:raise NotImplementedError(f'Noise command {note:02X}')
  #8670 uses JP86DE and an INCDE/JR continuation, unlike tone86DB.
  cost+=12+109+18
  if note==0xf6:
   cursor=read(cursor)|(read(cursor+1)<<8);cost+=4+7+6+7+6+10
  else:
   index=(read(cursor)+0x27)&255;cursor=(cursor+1)&65535
   assert offset+index<400
   cost+=6+7+4+7+15+10+11+7+4
   if r[offset+index]:cost+=12
   else:r[offset+index]=read(cursor);cost+=7+7+7
   cursor=(cursor+1)&65535;r[offset+index]=(r[offset+index]-1)&255;cost+=6+11+10
   if r[offset+index]:cursor=read(cursor)|(read(cursor+1)<<8);cost+=4+7+6+7+6+10
   else:cursor=(cursor+2)&65535;cost+=6+10
 else:raise ValueError('Noise command loop')
 cost+=7+7+10
 if note>=128:
  helper=noise_note_cost(r,note,offset);r=bytearray(helper['state']);cost+=17+helper['tstates']+10
  duration=read(cursor);cursor=(cursor+1)&65535;cost+=7+6+4+10
  if duration&128:
   r[offset+10]=r[offset+13];cursor=(cursor-1)&65535;cost+=19+19+6+12
  else:
   scale=r[offset+2];r[offset+10]=r[offset+13]=(duration*scale)&255
   cost+=17+(34 if scale==1 else 37+17*((scale-1)&255))+19+19
 else:
  scale=r[offset+2];r[offset+10]=r[offset+13]=(note*scale)&255
  cost+=17+(34 if scale==1 else 37+17*((scale-1)&255))+19+19
 r[offset+3:offset+5]=cursor.to_bytes(2,'little');cost+=19+19+20
 if r[offset]&2:cost+=11;return result()
 cost+=5+20
 if r[offset]&64:cost+=12
 else:r[offset]&=~32;cost+=7+23
 r[offset+14]=r[offset+15];r[offset+0x15]=0;cost+=19+19+4+19+20
 if r[offset+7]&128:cost+=11
 else:r[offset+0x1f]=0;cost+=5+19+10
 return result()
