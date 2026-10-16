"""Instruction-derived original bank6 tempo and fade state/cost models."""

def tempo_cost(state):
 r=bytearray(state);assert len(r)==400
 cost=10+7+4
 if not r[1]:return dict(state=bytes(r),tstates=cost+11)
 cost+=5+11;r[1]=(r[1]-1)&255
 if r[1]:return dict(state=bytes(r),tstates=cost+11)
 cost+=5+13+7+10+10+7;r[1]=r[2]
 for n in range(4):r[0x4a+n*0x30]=(r[0x4a+n*0x30]+1)&255;cost+=11+11+(8 if n==3 else 13)
 return dict(state=bytes(r),tstates=cost+10)

def stop_cost(state):
 r=bytearray(state);r[5:]=bytes(395);r[5]=0x80
 #83EF pushes3 regs,clears394 bytes from DE06,then emits10 PSG mute bytes.
 cost=11*3+10*3+10+(393*21+16)+10*3
 cost+=11*2+10+7+7+(9*21+16)+10*2+10+7+13+10
 return dict(state=bytes(r),tstates=cost)

def fade_cost(state):
 r=bytearray(state);assert len(r)==400
 cost=13+4
 if not r[0xb]:return dict(state=bytes(r),tstates=cost+11)
 cost+=5+13+4;counter=(r[0xc]-1)&255
 if counter:r[0xc]=counter;return dict(state=bytes(r),tstates=cost+7+13+10)
 cost+=12+13+13+13+4+13+10;r[0xc]=r[0xd];r[0xb]=(r[0xb]-1)&255
 if not r[0xb]:
  stopped=stop_cost(r);return dict(state=stopped['state'],tstates=cost+stopped['tstates'])
 cost+=10+10+7
 def volume(offset):
  value=(r[offset]+1)&255
  if value>=12:return 7+4+7+11
  r[offset]=value;return 7+4+7+5+7+10
 for n in range(3):cost+=17+volume(0x48+n*0x30)+11+(8 if n==2 else 13)
 cost+=10+volume(0x18)
 return dict(state=bytes(r),tstates=cost)
