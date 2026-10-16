"""Original8097 request priority arbitration state and instruction cost."""

def arbitration_cost(rom,state):
 r=bytearray(state);assert len(r)==400
 cost=10+14+14+17+17
 decisions=[]
 for offset in [6,7,8]:
  request=r[offset];index=request&127;cost+=7+7
  if not index:cost+=12;decision='empty'
  else:
   cost+=7+4+10+4+7+11+7+19
   priority=rom[0x18000+0xad5+index-1]
   if priority<r[0x11]:cost+=12;decision='rejected'
   else:
    cost+=7+7+19+7+19;r[0x11]=priority&127;r[5]=request;decision='accepted'
  cost+=4+7+6+10;r[offset]=0;decisions.append(decision)
 return dict(state=bytes(r),tstates=cost,decisions=decisions)
