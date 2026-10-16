"""Original80FF music/effect/control dispatch state and instruction costs."""
from audio_prefix_cost import stop_cost

POINTER_COST=4+7+11+11+7+6+7+4+10
CHANNEL_COPY_COST=sum([7,11,14,9*16,4,7,6,4,19,19,19,4,7,11,10,11,4,10,10])

def dispatch_cost(rom,state):
 r=bytearray(state);assert len(r)==400
 command=r[5];cost=13+8+10
 def read(address):return rom[0x18000+(address-0x8000)]
 def pointer(address):return read(address)|(read(address+1)<<8)
 def finish():
  r[5]=0x80
  return 7+13+10
 def copy_channel(offset,header):
  r[offset:offset+9]=bytes(read(header+i) for i in range(9))
  r[offset+9]=0x30;r[offset+10]=1;r[offset+0x27:offset+0x2a]=bytes(3)
  return CHANNEL_COPY_COST
 if not command&128:
  stopped=stop_cost(r);return dict(state=stopped['state'],tstates=cost+stopped['tstates'])
 cost+=7
 if command<0x90:
  cost+=12+7
  if command==0x80:return dict(state=bytes(r),tstates=cost+11)
  if command>0x8d:raise NotImplementedError(hex(command))
  cost+=5+4+17
  stopped=stop_cost(r);r=bytearray(stopped['state']);cost+=stopped['tstates']
  index=command-0x81;cost+=4+10+4+4+17+(7+11+7+10)+13+13+4
  r[1]=r[2]=read(0x8b09+index)
  cost+=10+17+POINTER_COST+7+6+10
  header=pointer(0x8b16+index*2);count=read(header);header+=1;assert 1<=count<=4
  for n in range(count):cost+=17+copy_channel(0x40+n*0x30,header+n*9)+(8 if n==count-1 else 13)
  cost+=finish()
  return dict(state=bytes(r),tstates=cost)
 cost+=7+7
 if command<0xad:
  cost+=12+13+7+10+17+POINTER_COST+7+6;r[0xf]=command
  header=pointer(0x8b30+(command-0x90)*2);count=read(header);header+=1;assert 1<=count<=3
  for n in range(count):
   channel=read(header+1);cost+=6+7+6+7
   if channel==0xa0:cost+=12+10+14;offset,background=0x100,0x70
   else:
    cost+=7+7
    if channel==0xc0:
     cost+=12+14+20
     if r[0x160]&64:cost+=12
     else:cost+=7+23+7+11;r[0x160]|=4
     cost+=10+14+12;offset,background=0x130,0xa0
    else:cost+=7+10+14+12;offset,background=0x160,0xd0
   cost+=17+23+copy_channel(offset,header)+(8 if n==count-1 else 13);r[background]|=4;header+=9
  cost+=12+finish()
  return dict(state=bytes(r),tstates=cost)
 cost+=7+7+10
 if command>=0xb5:
  stopped=stop_cost(r);return dict(state=stopped['state'],tstates=cost+stopped['tstates'])
 if command not in [0xb0,0xb1,0xb2,0xb3]:raise NotImplementedError(hex(command))
 cost+=7+10+17+POINTER_COST+4
 if command==0xb0:
  r[0xb:0xe]=bytes([12,18,18]);cost+=7+13+7+13+13+10+finish()
 elif command==0xb1:
  stopped=stop_cost(r);r=bytearray(stopped['state']);cost+=stopped['tstates']
 elif command==0xb2:
  cost+=14+10+7+10
  for n in range(3):r[0x103+n*0x30:0x105+n*0x30]=bytes([0x4e,0x81]);cost+=19+19+15+(8 if n==2 else 13)
  cost+=10
 else:
  r[0xe]=0;cost+=4+17+13+4+13+4+10
  if not r[0xf]&128:
   cost+=10+(12 if r[0xf]==0 else 7+10)+7+6+7+7+11
   r[0x130 if r[0xf]==0 else 0x160]=r[0xf]
  cost+=4+10+10+finish()
 return dict(state=bytes(r),tstates=cost)
