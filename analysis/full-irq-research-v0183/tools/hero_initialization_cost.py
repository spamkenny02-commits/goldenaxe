"""Original2C63 hero initialization semantics and instruction-derived T states."""

def hero_initialization_cost(rom,ram):
 mem=bytearray(ram);assert len(mem)==8192
 get=lambda address:mem[(address-0xc000)&8191]
 def put(address,value):mem[(address-0xc000)&8191]=value&255
 def word(address,value):put(address,value);put(address+1,value>>8)
 def lookup(address):return int.from_bytes(rom[address:address+2],'little')
 parts={};old_terrain=get(0xc041);selected=get(0xc0df);direction=get(0xc30a)
 assert selected<=16 and direction<=3 and get(0xc040)<=2
 for address in [0xc312,0xc310,0xc304,0xc30c,0xc30b]:put(address,0)
 for offset,value in enumerate([2,0,0xf0,3]):put(0xc300+offset,value)
 parts['initial_fields']=14+4+5*13+4*19
 #369F: previous terrain/selected secondary choose sprite descriptors.
 pose=13+7
 if old_terrain==3:
  pose+=12+sum([13,7,4,13,4,4,4,10,11,4,4,12,7,6,7,4,10,16,7,13,19,19,10])
  word(0xc043,lookup(0x3d67+direction*4));put(0xc042,5);word(0xc308,0x80a0)
 else:
  pose+=7+7+13+4
  c=0
  if selected==1:pose+=7+13+4+4;c=(get(0xc0e1)+1)&255
  else:pose+=12
  pose+=13+7
  if old_terrain==2:pose+=7+8;c|=4
  else:pose+=12
  pose+=sum([10,4,4,4,4,4,4])
  offset=(c*8)&255;carry=offset+0xa0>255
  pose+=11 if carry else 12
  word(0xc308,0x80a0+offset)
  pose+=sum([16,10,4,4,4,19,4,4,4,19,4,7,13,7])
  bitmap=(((c*4)|direction)*8)&255
  if old_terrain==5:pose+=7+4+7+4;bitmap&=0xe7
  else:pose+=12
  pose+=sum([11,11,7,6,7,4,16,7,8])
  pose+=7+4 if c&4 else 12
  pose+=13+10
  word(0xc043,lookup(0x3b67+bitmap*2));put(0xc042,5 if c&4 else 4)
 parts['pose']=17+pose
 #2D7C clears first byte then copies it through383 more bytes.
 parts['auxiliary_clear']=17+10+10+10+10+(382*21+16)+10
 mem[0x330:0x4b0]=bytes(384)
 defense=sum([13,4,4,4,13,4,4,4,4,13,4,4])
 defense+=7+4 if get(0xc0bf) else 12
 defense+=4+13
 put(0xc31a,((get(0xc0f2)-1)*2+(0 if get(0xc0bf) else (get(0xc0f1)-1)*4)))
 parts['defense']=defense
 attack=sum([10,7,7,6,11,7,4,4,11,11,11,10,11,7,10])
 parts['attack']=17+attack+13
 put(0xc319,rom[0x2d9e+selected*4+get(0xc0e0+selected)])
 x,y=get(0xc313),get(0xc311)
 contact=sum([13,4,13,4,4,7,4,4,4,4,4,7,4,4,4,4,4,4,7])
 contact+=7+8 if (x|y)&7 else 12
 contact+=4+13+10
 put(0xc06b,((x&8)>>3)|((y&8)>>2)|(128 if (x|y)&7 else 0))
 yy=(y-12)&248;xx=((x-12)&255)>>2&62
 low=(yy*8)&255
 routine=sum([19,4,7,4,7,11,11,11,19,4,4,4,7,4,4])
 routine+=11 if low+xx>255 else 12
 routine+=sum([10,11,7,4,7,10])
 address=0xd600+yy*8+xx
 contact+=17+routine+4+10+10
 for row in range(3):
  data=bytes(get(address+i) for i in range(8));mem[0x48+row*8:0x50+row*8]=data
  address+=8;contact+=8*16+7+4+4
  contact+=11 if (address&255)+56>255 else 12
  address+=56;contact+=13 if row<2 else 8
 contact+=10+11+16
 word(0xc060,address+0x29be)
 parts['contact_copy']=contact
 water=13+4
 if get(0xc0ec):water+=12
 else:
  water+=7+10+10
  for i in range(12):
   address=0xc049+i*2;water+=7+4
   if get(address)&32:water+=7+15;put(address,get(address)|128)
   else:water+=12
   water+=4+4+(13 if i<11 else 8)
 parts['water_collision_flags']=water
 classify=13+7
 graphics=get(0xc040)
 if graphics==1:classify+=12+4;terrain=0
 else:
  classify+=7
  classify+=12+14 if graphics==0 else 7+14+12
  table=0x2544 if graphics==0 else 0x2569;terrain=0
  for i,any_match in enumerate([True,False,False,True,True]):
   record=rom[table+i*4:table+i*4+4];pointer=int.from_bytes(record[:2],'little');count=record[2] or 256
   values=rom[pointer:pointer+count]
   def search(value):
    position=next((n+1 for n,a in enumerate(values) if a==value),None)
    return position,(position or count)*21-5
   p1,cost1=search(get(0xc052));helper=10+15+13+19+19+19+cost1
   matched=False
   if any_match and p1 is not None:helper+=12+19+10;matched=True
   elif not any_match and p1 is None:helper+=11
   else:
    helper+=7+12 if any_match else 5
    p2,cost2=search(get(0xc054));helper+=13+19+19+19+cost2
    helper+=5+19+10 if p2 is not None else 11
    matched=p2 is not None
   classify+=17+helper+(12 if matched else 7)
   if matched:terrain=record[3];break
  else:classify+=4
 put(0xc041,terrain);classify+=13
 parts['terrain_classifier']=classify
 earth=13+4
 if not get(0xc0f0):earth+=12
 else:
  earth+=7+13+10+7+7+8
  flags=get(0xc053)&get(0xc055)&0xc0
  if not flags&64:earth+=12
  else:
   earth+=7+4+(7 if flags&128 else 12)+10+7
   for i in range(12):
    address=0xc049+i*2;earth+=12
    if get(address)&64:earth+=7+15;put(address,get(address)&127);earth+=12 if flags&128 else 0
    else:
     earth+=12
     if flags&128:earth+=15;put(address,get(address)|128)
    earth+=6+6+(13 if i<11 else 8)
   if flags&128:earth+=12
 parts['earth_collision_flags_and_return']=earth+10
 return dict(foreground_tstates=sum(parts.values()),components=parts,ram=bytes(mem),scope='Original2C63/369F/2D7C/2D8A/230E/386E/3885;classes0..2,selected0..16,direction0..3. IRQ work excluded;input room map and hero state supplied.')
