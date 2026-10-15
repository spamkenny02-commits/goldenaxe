"""Original82C5 pitch/vibrato state,returned HL and instruction cost."""
from audio_dispatch_cost import POINTER_COST

def pitch_cost(rom,state,offset=0x40,return_address=0x8507):
 r=bytearray(state);assert len(r)==400
 def word(n):return int.from_bytes(r[offset+n:offset+n+2],'little')
 def setword(n,value):r[offset+n:offset+n+2]=(value&65535).to_bytes(2,'little')
 def read(a):
  a&=65535
  if a<0x8000:return rom[a]
  if a<0xc000:return rom[0x18000+(a&0x3fff)]
  if 0xde00<=a<0xdf90:return r[a-0xde00]
  raise NotImplementedError(f'Uncaptured pitch RAM {a:04X}')
 base=word(11);mode=r[offset+6];cost=19*3+4
 def result(hl,unwind=False):return dict(state=bytes(r),tstates=cost,hl=hl&65535,unwind=unwind,**({"de":base} if 0<mode<128 else {}))
 if not mode:cost+=11;return result(base)
 cost+=5+10
 if mode&128:
  cost+=23;r[offset+0x14]=(r[offset+0x14]-1)&255
  if r[offset+0x14]:cost+=11;return result(base)
  cost+=5+23+11+19+19+23+19+19+11+14
  r[offset+0x14]=1;r[offset+0x15]=(r[offset+0x15]-1)&255
  delta=word(0x12);table=word(0x10)
  if r[offset+0x15]:cost+=12
  else:
   cost+=7+19+19+19+4+7+4+8+4+11+19+19
   r[offset+0x15]=read(table+1);step=r[offset+0x16];step=step-256 if step&128 else step
   delta=(delta+step)&65535;setword(0x12,delta)
  cost+=10+11+23;r[offset+0x17]=(r[offset+0x17]-1)&255
  if r[offset+0x17]:cost+=11;return result(base+delta)
  cost+=5+19+19+19+8+19+10
  r[offset+0x17]=read(table+3);r[offset+0x16]=(-r[offset+0x16])&255
  return result(base+delta)
 cost+=4+4+10+17+POINTER_COST+12
 p=0x8a52+(mode-1)*2;table=read(p)|(read(p+1)<<8)
 for guard in range(256):
  value=read(table+r[offset+0x15]);cost+=11+19+17+(7+11+7+10)+10+8
  if value<128:
   cost+=12+7+4+11+23+10;r[offset+0x15]=(r[offset+0x15]+1)&255
   return result(base+value)
  cost+=7+7
  if value==0x83:
   cost+=12+6+7+12+19;base=(base+1)&65535;r[offset+0x15]=read(base);continue
  cost+=7
  if value>0x83:
   cost+=12+7+12+4+11+23+10;r[offset+0x15]=(r[offset+0x15]+1)&255
   return result(base+value-256)
  cost+=7+7
  if value==0x80:cost+=12+4+12+19;r[offset+0x15]=0;continue
  cost+=7+23+10+10;r[offset]|=32
  return result(return_address,True)
 raise ValueError('Pitch control loop did not terminate')
