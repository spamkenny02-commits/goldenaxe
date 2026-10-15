"""Original854B table envelope,including caller-frame unwind on81/82."""
from audio_dispatch_cost import POINTER_COST

def table_envelope_cost(rom,state,offset=0x40,de=0x8a0b):
 r=bytearray(state);assert len(r)==400
 def read(address):
  address&=65535
  if address<0x8000:return rom[address]
  if address<0xc000:return rom[0x18000+(address&0x3fff)]
  if 0xde00<=address<0xdf90:return r[address-0xde00]
  raise NotImplementedError(f'Uncaptured RAM {address:04X}')
 mode=r[offset+7];cost=19+4
 if not mode:return dict(state=bytes(r),tstates=cost+11,accumulator=0,de=de,unwind=False)
 assert mode<128
 cost+=5+10+4+10+17+POINTER_COST+12
 pointer=0x897f+(mode-1)*2;table=read(pointer)|(read(pointer+1)<<8)
 for guard in range(256):
  value=read(table+r[offset+0x1f]);cost+=11+19+17+(7+11+7+10)+10+8
  if value<128:
   r[offset+0x1f]=(r[offset+0x1f]+1)&255
   return dict(state=bytes(r),tstates=cost+12+23+10,accumulator=value,de=de,unwind=False)
  cost+=7+7
  if value==0x82:
   cost+=12+23+10+12+23+20;r[offset]|=16
   if r[offset]&4:return dict(state=bytes(r),tstates=cost+11,accumulator=value,de=de,unwind=True)
   return dict(state=bytes(r),tstates=cost+5+7+19+11+10,accumulator=(r[offset+1]+31)&255,de=de,unwind=True)
  cost+=7+7
  if value==0x81:
   r[offset]|=16
   return dict(state=bytes(r),tstates=cost+12+23+10+10,accumulator=value,de=de,unwind=True)
  cost+=7+7
  if value==0x80:cost+=12+4+12;r[offset+0x1f]=0
  else:
   cost+=7+6+7+12;de=(de+1)&65535;r[offset+0x1f]=read(de)
  cost+=19
 raise ValueError('Envelope control loop does not terminate within256 steps')
