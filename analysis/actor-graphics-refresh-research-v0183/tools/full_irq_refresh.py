"""Original gatedIRQ state/cost/M1 stages;explicit input,palette andreader metadata."""
from full_irq_cost import full_irq_cost

def full_irq_refresh(rom,state,palette_taken,palette_exits,joy,reset_bits,compensation,reader_tstates,reader_M1):
 result=full_irq_cost(rom,state,palette_taken,palette_exits,joy,reset_bits,compensation,reader_tstates)
 r=bytearray(state);stages={}
 def index(a):
  if 0xc000<=a<0xc050:return a-0xc000
  if 0xdd00<=a<0xde00:return 80+a-0xdd00
  raise NotImplementedError(f'Uncaptured IRQ RAM {a:04X}')
 def read(a):return r[index(a)]
 def write(a,v):r[index(a)]=v&255
 #The three12T OUT(C),B are ED instructions,not ordinary conditional jumps.
 stages['SAT64']=3+2+3*(2+2)+9+64*2+1
 stages['SAT128']=4+1+128*2+1
 tile=2
 if not r[0x42]:tile+=1
 else:
  bank=r[0x42];pointer=int.from_bytes(r[0x43:0x45],'little')
  if bank>=16 or pointer>=0xc000:raise NotImplementedError('Uncaptured tile-count bank/RAM')
  a=pointer if pointer<0x8000 else bank*0x4000+(pointer&0x3fff);count=rom[a] or 256
  #LD HL,(nn) is one fetch;each24 OUTI is two,each eight OUT(n),A is one.
  tile+=12+count*(24*2+8+1+1)+1;r[0x42]=0
 stages['tiles']=1+tile
 hud=2
 if r[0x33]:hud+=1
 else:
  hud+=3
  if not r[0x45]&3:hud+=1
  else:hud+=14+60*2+1;r[0x45]=0
 stages['HUD']=1+hud
 palette=2
 if r[0x33]:assert palette_taken==palette_exits==0;palette+=1
 else:
  assert palette_exits==1
  palette+=4+(1 if compensation else 2)+palette_taken*3+3+6+32*3
 stages['palette']=palette
 #16T LD HL,(nn) andLD(nn),HL are ordinary opcodes,not ED-prefixed LDI.
 queue=4;pointer=int.from_bytes(r[0x34:0x36],'little');write(pointer,0);iy=0xdd00
 for guard in range(128):
  command=read(iy);queue+=4
  if command==1:
   queue+=15;bank=read(iy+1);count=read(iy+6) or 256
   if bank&128:queue+=6+2+count*(1+32*3+1+1)+3+6+1
   else:queue+=3+count*(1+32*3+1+1)+4
   iy+=7
  elif not command:
   queue+=5;r[0x34:0x36]=b'\x00\xdd';write(0xdd00,0);break
  else:
   height=read(iy+1) or 256;width=(read(iy+2)*2)&255;width=width or 256
   queue+=6+height*(12+width*4+5)+4;write(iy+1,0);iy+=5
 else:raise ValueError('IRQ queue did not terminate')
 stages['queue']=1+queue;stages['map_audio']=3;stages['audio']=1+reader_M1
 post=2+(4 if r[0x1c] else 1)+22+(3 if r[0x30] else 1)+5
 stages['post_audio']=post
 result.update(M1_stages=stages,to_RET_M1=sum(stages.values()),whole_IRQ_M1=6+sum(stages.values())+1,GPG_acknowledge_M1=0)
 return result
