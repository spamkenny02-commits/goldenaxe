"""Original0137 full gatedIRQ instruction/state model;explicit palette decisions/input."""
def full_irq_cost(rom,state,palette_taken,palette_exits,joy,reset_bits,compensation,reader_tstates):
 r=bytearray(state);assert len(r)==336 and r[0x2e] and reset_bits==16
 def index(a):
  if 0xc000<=a<0xc050:return a-0xc000
  if 0xdd00<=a<0xde00:return 80+a-0xdd00
  raise NotImplementedError(f'Uncaptured IRQ RAM {a:04X}')
 def read(a):return r[index(a)]
 def write(a,v):r[index(a)]=v&255
 stages={}
 stages['SAT64']=27+10+10+3*(16+12)+7+13+4+11+7+11+7+10+17+64*16+10
 stages['SAT128']=4+11+4+11+17+128*16+10
 tile=13+4
 if not r[0x42]:tile+=11
 else:
  tile+=5+13+16+7+6+7+11+7+11+4+13+7
  bank=r[0x42];pointer=int.from_bytes(r[0x43:0x45],'little')
  if bank>=16 or pointer>=0xc000:raise NotImplementedError('Uncaptured tile-count bank/RAM')
  a=pointer if pointer<0x8000 else bank*0x4000+(pointer&0x3fff)
  count=rom[a] or 256;r[0x42]=0;tile+=count*(24*16+8*11+4+10)+10
 stages['tiles']=17+tile
 hud=13+4
 if r[0x33]:hud+=11
 else:
  hud+=5+13+7
  if not r[0x45]&3:hud+=11
  else:r[0x45]=0;hud+=5+4+4+7+11+4+7+11+4+13+7+7+13+10+60*16+10
 stages['HUD']=17+hud
 palette=13+4
 if r[0x33]:
  assert palette_taken==palette_exits==0;palette+=12
 else:
  assert palette_exits==1;palette+=7+10+13+4+(12 if compensation else 7+4)
  palette+=palette_taken*(11+4+12)+(11+4+7)+4+11+7+11+10+10+32*(16+13)-5
 stages['palette']=palette
 queue=16+10+14;pointer=int.from_bytes(r[0x34:0x36],'little');write(pointer,0);iy=0xdd00
 for guard in range(128):
  command=read(iy);queue+=19+7+10
  if command==1:
   queue+=7+19+11+19+11+19+19+19+4+10
   bank=read(iy+1);count=read(iy+6) or 256;loop=count*(7+32*(16+13)-5+4+12)-5
   if bank&128:queue+=17+(4+13+7+13+10)+19+loop+10+15+17+(13+7+13+4+10)+12
   else:queue+=13+19+loop+10+15+12
   iy+=7
  elif command==0:
   queue+=10+10+16+7+10;r[0x34:0x36]=(0xdd00).to_bytes(2,'little');write(0xdd00,0);break
  else:
   queue+=10+7+19+19;height=read(iy+1) or 256;width=(read(iy+2)*2)&255;width=width or 256
   queue+=height*(4+10+11+4+11+4+11+4+4+19+4+width*(16+4+10)+10+11+23+12)-5+10+15+10
   write(iy+1,0);iy+=5
 else:raise ValueError('IRQ queue did not terminate')
 stages['queue']=17+queue;stages['map_audio']=4+7+13;stages['audio']=17+reader_tstates
 post=13+4
 pause=0
 if r[0x1c]:pause=1;r[0x1c]-=1;post+=7+4+13+7
 else:post+=12
 previous=r[0x22];r[0x22]=pause;r[0x23]=pause&(~previous&255)
 previous=r[0x20];r[0x20]=joy;r[0x21]=joy&(~previous&255)
 post+=10+4+7+7+6+4+7+11+4+7+10+4+7+7+6+4+7+11+7+10+13+4
 if r[0x30]:r[0x30]-=1;post+=7+4+13
 else:post+=12
 r[0x2f]=(r[0x2f]+1)&255;r[0x2e]=0;post+=10+11+4+13+10
 stages['post_audio']=post
 return dict(state=bytes(r),stages=stages,to_RET_tstates=sum(stages.values()),whole_IRQ_tstates=72+sum(stages.values())+10)
