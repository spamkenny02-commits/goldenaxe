"""Original8679 noise-note selection,400-byte state and exact instruction cost."""
def noise_note_cost(state,note,offset=0xd0):
 r=bytearray(state);cost=0
 for bit in range(6):
  cost+=8
  if note&(1<<bit):
   cost+=12+7*3+(0 if bit==0 else 12)
   mode,volume,noise=[(1,4,0xe4),(3,6,0xe4),(1,1,0xe6),(2,3,0xe5),(3,3,0xe6),(4,4,0xe4)][bit]
   r[offset+7]=mode;r[offset+8]=(r[0x18]+volume)&255
   cost+=19+13+4+19+20
   if r[offset]&4:cost+=11
   else:r[0x13]=(r[0x17]+noise)&255;cost+=5+13+4+13+11+10
   return dict(state=bytes(r),tstates=cost)
  cost+=7
 r[offset]|=16;cost+=10+23+20
 cost+=11 if r[offset]&4 else 5+7+19+11+10
 return dict(state=bytes(r),tstates=cost)
