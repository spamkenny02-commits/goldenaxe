"""Instruction-derived bank2 844D projection costs, including four color lookups."""
def projection_cost(cells,colors,row,col):
 total=sum([4,4,4,4,4,4,4,4,4,4,4,7,10,11]) #844D..845D
 maximum=0
 for offset in [row*32+col*2,row*32+col*2+1,row*32+col*2+16,row*32+col*2+17]:
  cell=cells[offset];pair=colors[cell>>1];value=(pair&15) if cell&1 else pair>>4
  #CALL84C6; LD A,(HL),LD E,A,SRL A,PUSH HL,LD HL,84DE; RST08.
  total+=17+7+4+8+11+10+11+4+4+(11 if 0xde+(cell>>1)>=256 else 12)+7+6+7+4+10
  total+=10+8 #POP HL;BIT0,E
  total+=(12 if cell&1 else 7+4*4)+7+4 #JR,RRCAx4,AND15,CPD
  total+=11 if value<maximum else 5+4+10
  maximum=max(maximum,value)
 #INC HL twice,LD A15,ADDAL,LDLA between calls; LDA D,PUSH BC.
 total+=6+7+4+4+6+4+11
 # Four plane masks, RR(HL) repeated col+1 times.
 total+=4+4+10+7
 total+=4*(10+4+4+(col+1)*28-5+6+4+12)-5
 #8485..84B1, address from room/row and bank tile position.
 total+=sum([13,7,7,4,4,4,4,4,4,4,4,7,4,4,4,4,7,4,4,4,13,7,4,7,11,11,11,11,11,11,4,10,7])
 # Four read/OR/write planes; RST28 includes DI/EI.
 total+=4*(8+(11+4+4+11+4+11+4+10)+8+11+7+11+(11+4+4+11+4+11+4+10)+10+11+6+6+13)-5
 return total+10+10 #POPBC;RET
# Transform21 dispatcher cost and cell effects, restricted to original routine opcodes.
def transformation_cost(rom,record,cells):
 from world_map_loading_cost import tile_patch_cost
 a=record[2]*2;b=c=h=l=0;d=0xdc;e=record[1];z=carry=False;stack=[];cost=103
 pc=int.from_bytes(rom[0x1a8a+a:0x1a8c+a],'little')
 def word(p):return int.from_bytes(rom[p:p+2],'little')
 for guard in range(1000):
  if pc==0x1b0e:
   address=(d<<8)|e
   if 0xdc00<=address<0xde00:cells[address-0xdc00]=a
   cost+=tile_patch_cost(e)
   if not stack:return cost
   pc=stack.pop();continue
  op=rom[pc];pc+=1
  if op==0xc9:
   cost+=10
   if not stack:return cost
   pc=stack.pop()
  elif op==0xcd:stack.append(pc+2);pc=word(pc);cost+=17
  elif op==0xc3:pc=word(pc);cost+=10
  elif op==0xca:
   target=word(pc);pc=target if z else pc+2;cost+=10
  elif op in [0x18,0x30]:
   offset=rom[pc];offset=offset if offset<128 else offset-256;pc+=1;take=op==0x18 or not carry
   if take:pc+=offset
   cost+=12 if take else 7
  elif op==0x10:
   offset=rom[pc];offset=offset if offset<128 else offset-256;pc+=1;b=(b-1)&255
   if b:pc+=offset
   cost+=13 if b else 8
  elif op in [0x3e,0x06,0x1e]:
   v=rom[pc];pc+=1
   if op==0x3e:a=v
   elif op==0x06:b=v
   else:e=v
   cost+=7
  elif op in [0x21,0x01]:
   v=word(pc);pc+=2
   if op==0x21:h,l=v>>8,v&255
   else:b,c=v>>8,v&255
   cost+=10
  elif op==0x3a:
   address=word(pc);pc+=2;a=record[address-0xc06e];cost+=13
  elif op==0x32:
   address=word(pc);pc+=2;cells[address-0xdc00]=a;cost+=13
  elif op==0xaf:a=0;z=True;carry=False;cost+=4
  elif op==0x5f:e=a;cost+=4
  elif op==0x78:a=b;cost+=4
  elif op==0x79:a=c;cost+=4
  elif op==0x7b:a=e;cost+=4
  elif op==0x7e:
   address=(h<<8)|l;a=cells[address-0xdc00] if address>=0xdc00 else rom[address];cost+=7
  elif op==0x1a:a=cells[((d<<8)|e)-0xdc00];cost+=7
  elif op==0xc6:
   value=a+rom[pc];pc+=1;a=value&255;carry=value>255;z=not a;cost+=7
  elif op==0x19:
   value=((h<<8)|l)+((d<<8)|e);h,l=(value>>8)&255,value&255;carry=value>65535;cost+=11
  elif op==0xeb:h,d=d,h;l,e=e,l;cost+=4
  elif op==0x13:value=(((d<<8)|e)+1)&65535;d,e=value>>8,value&255;cost+=6
  elif op==0x23:value=(((h<<8)|l)+1)&65535;h,l=value>>8,value&255;cost+=6
  elif op==0xbe:
   value=rom[(h<<8)|l];z=a==value;carry=a<value;cost+=7
  else:raise AssertionError((hex(pc-1),hex(op)))
 raise AssertionError('Original transformation did not return')

def room_decode_cost(rom,room,flag,ice=0,previous_room=0):
 from ram_plane_loading_cost import ram_plane_cost
 from extract_title import rle_planes
 bank=8+(room>>7);table=bank*0x4000+(room*2&255);pointer=int.from_bytes(rom[table:table+2],'little');source=bank*0x4000+(pointer&0x3fff)
 cells=bytearray(512);rle_planes(rom,source,cells,0,1)
 classify=sum([13,4,7,7,13,7,7,7,13,7,7,7,7,4,13,10])
 total=44+17+classify+sum([16,11,4,7,13,7,7,6,7,4,10,7,17])+ram_plane_cost(rom,source,0xdc00,1)['tstates']
 def metadata(flag):
  subtotal=sum([17,13,4,11,7,13,20,4,4,10,12,10]);p=0xbb62
  while rom[p] and rom[p]!=room:subtotal+=7+4+7+4+7+11+12;p+=4
  if rom[p]:subtotal+=7+4+7+4+12+6;record=rom[p+1:p+4]
  else:subtotal+=7+4+12+10+12;record=rom[0x199e:0x19a1]
  subtotal+=10+3*16+13+4+12
  subtotal+=17+sum([16,13,7,12,7,10,4,4,7,4,7,4,4,7,10])
  subtotal+=17+transformation_cost(rom,record,cells) if flag else 10
  subtotal+=sum([4,13,13,7,12,10])
  return subtotal
 total+=17+metadata(flag)
 if not ice:
  terrain=sum([13,4,5,13,4,7,10,10,10,11,11,163,10,10,10,163,10])
 else:
  terrain=sum([13,4,5,13,4,12,13,4,5,10,10,10,163,10,7,163,13,10,10,58]) #CPIR3/miss or earlier match corrected below
  pos=rom[0x1a79:0x1a7c].find(bytes([room]))
  if pos>=0:
   terrain-=58;terrain+=(pos+1)*21-5+5 #RET nz not taken5
   terrain+=17+sum([17,16,13,7,12,7,10,4,4,7,4,7,4,4,7,10,7,10])+10+metadata(True) #193D then JP1976
  else:terrain+=11 #RET nz
 total+=17+17+terrain+17+sum([20,10,4,15,11])
 if room==0xbf:
  total-=11;total+=5+10+13+7
  for pos in range(3):
   total+=7+6+7+6
   if previous_room==rom[0x1a2a+pos*2]:total+=12+4+13+10;cells[0x28]=rom[0x1a2b+pos*2];break
   total+=7+(13 if pos<2 else 8)
  else:total+=10
 total+=10 #1A02 RET
 total+=10+10+16+4*10+10
 return total,bytes(cells[:160])
def room_projection_cost(cells,colors):
 total=7
 for row in range(5):
  total+=7
  for col in range(8):total+=7+13+17+projection_cost(cells,colors,row,col)+4+4+7+(12 if col<7 else 7)
  total+=4+4+7+(12 if row<4 else 7)
 return total

def room_loop_tail(room):
 total=10+16+6+16+(8 if room&15==14 else 13)
 if room&15==14:total+=16+6+16+4+4+(7 if room==254 else 12+7)
 return total


def restore_cells_cost():
 #3250..326A: POP/restore room, enable SRAM, LDIR160, disable SRAM,color.
 return 10+16+(17+4+13+7+13+10)+10+10+10+(159*21+16)+(17+13+7+13+4+10)+7+13
