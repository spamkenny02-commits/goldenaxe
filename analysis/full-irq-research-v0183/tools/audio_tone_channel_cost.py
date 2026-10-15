"""Original84C7 tone-channel composition,explicit entryDE for table dependencies."""
from audio_note_sequence_cost import note_sequence_cost
from audio_pitch_cost import pitch_cost
from audio_adsr_cost import adsr_cost
from audio_table_envelope_cost import table_envelope_cost

def tone_channel_cost(rom,state,offset=0x40,de=0x8a0b):
 r=bytearray(state);assert len(r)==400
 def read(a):
  a&=65535
  if a<0x8000:return rom[a]
  if a<0xc000:return rom[0x18000+(a&0x3fff)]
  if 0xde00<=a<0xdf90:return r[a-0xde00]
  raise NotImplementedError(f'Uncaptured tone RAM {a:04X}')
 def result():return dict(state=bytes(r),tstates=cost,unwind=False,de=de)
 r[offset+10]=(r[offset+10]-1)&255;cost=23
 pitch=True
 if not r[offset+10]:
  cost+=7+17;sequence=note_sequence_cost(rom,r,offset);r=bytearray(sequence['state']);cost+=sequence['tstates']
  de=sequence['de']
  if sequence.get('unwind',False):return result()
  de=int.from_bytes(r[offset+3:offset+5],'little')
  for bit in [16,4]:
   cost+=20
   if r[offset]&bit:cost+=11;return result()
   cost+=5
  cost+=17+20
  if not r[offset+6]&128:cost+=11
  else:
   cost+=5+20
   if r[offset]&2:cost+=11
   else:
    cost+=5+19+19+15+10+7+7+11+4+3*16+7+8+7+4+19+19+10
    pointer=int.from_bytes(r[offset+0x10:offset+0x12],'little')
    r[offset+0x14:offset+0x17]=bytes(read(pointer+i) for i in range(3))
    r[offset+0x17]=read(pointer+3)>>1;r[offset+0x12:offset+0x14]=bytes(2);de=0xde00+offset+0x17
  cost+=17+20
  if not r[offset+7]&128:cost+=11
  else:
   cost+=5+20
   if r[offset]&2:cost+=11
   else:
    cost+=5+20
    if r[offset+0x1d]&128:cost+=11
    else:r[offset+0x1f]=255;r[offset+0x1d]=16|r[offset+0x1e];cost+=5+7+19+7+19+19+10
  cost+=12
 else:
  cost+=12+20
  if r[offset]&4:cost+=11;return result()
  cost+=5+19+4
  if not r[offset+14]:cost+=12
  else:
   cost+=7+23;r[offset+14]=(r[offset+14]-1)&255
   if r[offset+14]:cost+=10
   else:
    cost+=17+20
    if r[offset]&2:cost+=11
    else:
     cost+=5+20+10
     if r[offset+7]&128:r[offset+0x1d]=(r[offset+0x1d]&15)|128;cost+=19+7+7+19+10
     else:
      r[offset]|=16;cost+=23+20
      cost+=11 if r[offset]&4 else 5+7+19+11+10
  cost+=19+4
  if not r[offset+6]:cost+=12;pitch=False
  else:
   cost+=7+20
   if r[offset]&32:cost+=12;pitch=False
   else:cost+=7
 if pitch:
  cost+=20
  if r[offset]&64:cost+=12
  else:
   cost+=7+17;value=pitch_cost(rom,r,offset);r=bytearray(value['state']);cost+=value['tstates']
   if value.get('unwind',False):de=value['de'];return result()
   transpose=r[offset+0x25];de=transpose if transpose<128 else transpose|0xff00
   cost+=7+19+4+10+(4 if transpose&128 else 0)+4+11+19+7
   cost+=7+7 if r[offset+1]==0xe0 else 12
   cost+=4+4+7+4+11+4+7+4+4*4+11
 cost+=17
 envelope=adsr_cost(r,offset,de) if r[offset+7]&128 else table_envelope_cost(rom,r,offset,de)
 r=bytearray(envelope['state']);cost+=envelope['tstates'];de=envelope.get('de',de)
 if envelope.get('unwind',False):return result()
 for bit in [4,16]:
  cost+=20
  if r[offset]&bit:cost+=11;return result()
  cost+=5
 volume=(envelope['accumulator']+r[offset+8])&255;cost+=19+8+(7+7 if volume&16 else 12)+19+7+11+10
 return result()
