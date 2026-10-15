"""Original854B ADSR state,returned accumulator and instruction cost."""

def adsr_cost(state,offset=0x40):
 r=bytearray(state);assert len(r)==400
 mode=r[offset+7];cost=19+4
 if not mode:return dict(state=bytes(r),tstates=cost+11,accumulator=0)
 if not mode&128:raise NotImplementedError('Table envelopes require their stream/stack model')
 cost+=5+10;flags=r[offset+0x1d];value=r[offset+0x1f]
 cost+=20
 if flags&16:
  cost+=7+19+19+4;step=r[offset+0x20]
  if value>=step:cost+=12;value-=step
  else:cost+=7+4;value=0
  cost+=4+19;r[offset+0x1f]=value
  if value:cost+=12
  else:cost+=7+19+7+19+12;r[offset+0x1d]^=0x30
 else:
  cost+=12+20
  if flags&32:
   cost+=7+19+19+19+4;limit=r[offset+0x22];value+=r[offset+0x21]
   if value>255:cost+=12+4;value=limit
   else:
    cost+=7+4
    if value<limit:cost+=12
    else:cost+=7+4;value=limit
   cost+=4+19;r[offset+0x1f]=value
   if value!=limit:cost+=12
   else:
    cost+=7+19+20
    if flags&8:cost+=7+7+12;r[offset+0x1d]^=0x30
    else:cost+=12+7;r[offset+0x1d]^=0x60
    cost+=19+12
  else:
   cost+=12+20
   if flags&64:
    cost+=7+19+19+4;value+=r[offset+0x23]
    if value<=255:cost+=12
    else:cost+=7+7;value=255
    cost+=7+19;r[offset+0x1f]=value
    if value!=255:cost+=12
    else:cost+=7+19+7+19+12;r[offset+0x1d]&=0x8f
   else:
    cost+=12+19+19+4;value+=r[offset+0x24]
    if value<=255:cost+=12+19;r[offset+0x1f]=value
    else:
     cost+=7+19+7+19+7+19+10;r[offset+0x1d]&=15;r[offset+0x1f]=255
     #863E terminates the channel and optionally emits a PSG mute byte.
     cost+=23+20;r[offset]|=16
     if r[offset]&4:return dict(state=bytes(r),tstates=cost+11,accumulator=255)
     a=(r[offset+1]+31)&255
     return dict(state=bytes(r),tstates=cost+5+7+19+11+10,accumulator=a)
 cost+=19+4*4+7+10
 return dict(state=bytes(r),tstates=cost,accumulator=r[offset+0x1f]>>4)
