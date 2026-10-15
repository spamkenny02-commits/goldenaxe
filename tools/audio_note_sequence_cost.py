"""Original8357 notes, E7/F7/F8/F9 control and F1/F2 without restoration8211."""
from audio_dispatch_cost import POINTER_COST

def note_sequence_cost(rom,state,offset=0x40):
 r=bytearray(state);assert len(r)==400
 def read(a):
  a&=65535
  if a<0x8000:return rom[a]
  if a<0xc000:return rom[0x18000+(a&0x3fff)]
  if 0xde00<=a<0xdf90:return r[a-0xde00]
  raise NotImplementedError(f'Uncaptured stream RAM {a:04X}')
 def word(n):return int.from_bytes(r[offset+n:offset+n+2],'little')
 def setword(n,value):r[offset+n:offset+n+2]=(value&65535).to_bytes(2,'little')
 def multiply(value):
  scale=r[offset+2]
  return (value*scale)&255,34 if scale==1 else 37+17*((scale-1)&255)
 cursor=word(3);r[offset]&=~18;cost=23+23+19+19
 for guard in range(256):
  note=read(cursor);cursor=(cursor+1)&65535;cost+=7+6+7+10
  if note<0xe0:break
  if note not in [0xe7,0xf1,0xf2,0xf7,0xf8,0xf9]:raise NotImplementedError(f'Command {note:02X}')
  if note in [0xf1,0xf2]:
   if r[0x0e]:raise NotImplementedError(f'Command {note:02X} restoration8211')
   cost+=sum([10,11,7,10,4,4,7,11,7,6,7,4,7,4])
   if note==0xf1:r[0x12]=128;cost+=7+13
   channel=r[offset+1];cost+=19+7
   if channel==0xa0:cost+=12+10;background=0x70
   else:
    cost+=7+7
    if channel==0xc0:
     cost+=12+10+12
     if r[0x160]&128:cost+=12;background=0x160
     else:cost+=7+10+12;background=0xa0
    else:
     cost+=7+20
     if r[offset]&64:cost+=12
     else:
      cost+=7+10+12+10
      if not r[0x130]&128:
       cost+=10+15+15+15+10+10
       r[0xa0]=(r[0xa0]&~68)|16;r[0x130]=0
     cost+=10+12;background=0xd0
   r[background]=(r[background]&~4)|16;r[0x11]=0;r[offset]=0
   cost+=15+15+7+11+4+13+19+13+4+12+10+10+10
   return dict(state=bytes(r),tstates=cost,unwind=True)
  cost+=sum([10,11,7,10,4,4,7,11,7,6,7,4,7,4])+6+10
  if note==0xe7:cost+=23+6+10;r[offset]|=2
  elif note==0xf7:
   index=(read(cursor)+0x27)&255;cursor=(cursor+1)&65535
   assert offset+index<400
   cost+=6+7+4+7+15+10+11+7+4
   if r[offset+index]:cost+=12
   else:cost+=7+7+7;r[offset+index]=read(cursor)
   cursor=(cursor+1)&65535;r[offset+index]=(r[offset+index]-1)&255;cost+=6+11+10
   if r[offset+index]:cost+=4+7+6+7+6+10;cursor=read(cursor)|(read(cursor+1)<<8)
   else:cost+=6+10;cursor=(cursor+2)&65535
  elif note==0xf8:
   target=read(cursor)|(read(cursor+1)<<8);stack=(r[offset+9]-2)&255
   assert offset+stack+1<400
   setword(stack,cursor+1);r[offset+9]=stack;cursor=target
   cost+=sum([4,6,7,4,11,15,10,23,19,23,7,11,7,6,7,10,6,10])
  else:
   stack=r[offset+9];assert offset+stack+1<400
   cursor=(word(stack)+1)&65535;r[offset+9]=(stack+2)&255
   cost+=15+10+19+7+11+7+6+7+23+23+10
 else:raise ValueError('Tie command loop')
 cost+=20+10
 if r[offset]&8:
  low=read(cursor);cursor=(cursor+1)&65535;frequency=(note<<8)|low
  cost+=4+7+6+4+4
  if not frequency:cost+=12
  else:
   cost+=7+7+19+4+4+10+(4 if r[offset+5]&128 else 0)+11
   transpose=r[offset+5];frequency+=transpose-256 if transpose&128 else transpose
  setword(11,frequency);cost+=19+19+7+6+10
  duration=read(cursor);cursor=(cursor+1)&65535
  duration,work=multiply(duration);cost+=17+work+19+19;r[offset+10]=r[offset+13]=duration
 else:
  cost+=7
  if note<128:
   cost+=12;duration,work=multiply(note);cost+=17+work+19+19;r[offset+10]=r[offset+13]=duration
  else:
   cost+=7
   if note==128:
    cost+=12+17+20
    if r[offset]&2:cost+=11
    else:
     cost+=5+20+10
     if r[offset+7]&128:cost+=19+7+7+19+10;r[offset+0x1d]=(r[offset+0x1d]&15)|128
     else:
      cost+=23+20;r[offset]|=16
      cost+=11 if r[offset]&4 else 5+7+19+11+10
    cost+=12
   else:
    cost+=7+4+19+7+19+4+17+7+19+10+POINTER_COST+19+19
    r[offset+0x1d]&=127;index=((note&127)+r[offset+5])&255;address=0x843d+index*2
    setword(11,read(address)|(read(address+1)<<8))
   duration=read(cursor);cursor=(cursor+1)&65535;cost+=7+6+4+10
   if duration&128:
    r[offset+10]=r[offset+13];cursor=(cursor-1)&65535;cost+=19+19+6+12
   else:
    duration,work=multiply(duration);cost+=17+work+19+19;r[offset+10]=r[offset+13]=duration
 setword(3,cursor);cost+=19+19+20
 if r[offset]&2:return dict(state=bytes(r),tstates=cost+11)
 cost+=5+20
 if r[offset]&64:cost+=12
 else:cost+=7+23;r[offset]&=~32
 cost+=19+19+4+19+20;r[offset+14]=r[offset+15];r[offset+0x15]=0
 if r[offset+7]&128:cost+=11
 else:cost+=5+19+10;r[offset+0x1f]=0
 return dict(state=bytes(r),tstates=cost)
