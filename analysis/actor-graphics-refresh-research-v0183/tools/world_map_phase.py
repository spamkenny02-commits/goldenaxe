"""Instruction phase chain: source16D0 graphics followed by190B world map."""
from foreground_phase import ForegroundPhase
from graphics_load_phase import predict_graphics_load,execute,plane_decode,ldir
from world_map_loading_cost import world_map_cost,tile_patch_cost,ROOMS
from extract_title import rle_planes
from actor_loading_cost import rle_cost

def patch(cpu,coordinate,tiles=None,tile=0):
 before=cpu.foreground_tstates
 for t in [11,11,7,4,7,11,11,11,10,11,11,4,7,4,7,4,11,11,11,4,7,4,4,4,11,10,11,4,16,7,7,4,7,4,7,4,7,4,7,4,16,10]:cpu.execute(t,'M1_1' if t==16 else None) #2A/22 are ordinary LD HL memory opcodes.
 execute(cpu,[16]*4+[7,4,4])
 address=0xd600+(coordinate&0xf0)*8+(coordinate&15)*4
 execute(cpu,[12] if (address+4&255)+60<256 else [7,4])
 execute(cpu,[16]*4+[10,10,10])
 assert cpu.foreground_tstates-before==tile_patch_cost(coordinate)
 pointer=int.from_bytes(cpu.ram[0x34:0x36],'little');offset=80+pointer-0xdd00
 assert 80<=offset<=331
 cpu.ram[offset:offset+5]=bytes([2,2,2,address&255,address>>8]);cpu.ram[0x34:0x36]=(pointer+5).to_bytes(2,'little')
 if coordinate==255:
  assert tiles is not None
  for row in range(2):
   dest=address+row*64;assert 0xdd00<=dest<=0xddfc
   offset=80+dest-0xdd00;cpu.ram[offset:offset+4]=tiles[tile*8+row*4:tile*8+row*4+4]

def predict_world_map(rom,phase,ram,sound,room,flags=1,cpu_factory=ForegroundPhase,graphics_model=predict_graphics_load):
 assert room in ROOMS and flags&1 and rom[0x4d]==1
 points=graphics_model(rom,phase,ram,sound);prefix=points[0x24b9]
 cpu=cpu_factory(rom,prefix['phase'],prefix['ram'],prefix['sound'])
 def checkpoint(pc):
  cpu.checkpoint();r=cpu.result();r['wall_master_cycles']+=prefix['wall_master_cycles'];r['foreground_tstates']+=prefix['foreground_tstates'];r['IRQ_tstates']+=prefix['IRQ_tstates']
  for k in ['foreground_M1','IRQ_M1']:
   if k in r:r[k]+=prefix[k]
  r['events']=prefix['events']+[dict(e,entry_offset_master=e['entry_offset_master']+prefix['wall_master_cycles']) for e in r['events']];points[pc]=r
 cpu.execute(17) #CALL190B
 execute(cpu,[11]*4+[17,13,4,7,7,13,7,7,7,13,7,7,7,7,4,13,10])
 cpu.execute(16,'M1_1');execute(cpu,[11,4,7,13,7,7,6,7,4,10,7,17]) #LD HL,(C0B9).
 bank=8+(room>>7);table=bank*0x4000+(room*2&255);pc=int.from_bytes(rom[table:table+2],'little');source=bank*0x4000+(pc&0x3fff)
 plane_decode(cpu,source,0xdc00,1);checkpoint(0x192a)
 execute(cpu,[17,17,13,4,11,7,13,20,4,4,10,12,10])
 p=0xbb62
 while rom[p] and rom[p]!=room:execute(cpu,[7,4,7,4,7,11,12]);p+=4
 if rom[p]:execute(cpu,[7,4,7,4,12,6]);record=rom[p+1:p+4]
 else:execute(cpu,[7,4,12,10,12]);record=rom[0x199e:0x19a1]
 execute(cpu,[10,16,16,16,13,4,12,17]);cpu.execute(16,'M1_1');execute(cpu,[13,7,12,7,10,4,4,7,4,7,4,4,7,10]) #Three LDI then LD HL,(C0B9).
 execute(cpu,[17,20,4,7,4,10,10,4,4,12,7,6,7,4,4])
 coordinate=record[1];kind=record[2];assert kind in [0,4]
 tiles=bytearray(2048);meta_source=rle_cost(rom,0x3c010,0x4000)['source_end'];rle_planes(rom,meta_source,tiles,0,2)
 execute(cpu,[4,12] if kind==0 else [7]);cpu.execute(17);patch(cpu,coordinate,tiles,0 if kind==0 else 4)
 execute(cpu,[10,11,4,7,10,7]);cells=bytearray(512);rle_planes(rom,source,cells,0,1);target=coordinate+16
 for n in range(4):
  execute(cpu,[7,6,10])
  if cells[target]==rom[0x1b05+n*2]:cpu.execute(7);patch(cpu,target);break
  execute(cpu,[6,13 if n<3 else 8])
 else:cpu.execute(10)
 cpu.execute(4);cpu.execute(13);cpu.ram[80]=0;execute(cpu,[13,7,12,10]);checkpoint(0x192d)
 execute(cpu,[17,17,13,4,5,13,4,7,10,10,10,11,11]);ldir(cpu,8);execute(cpu,[10,10,10]);ldir(cpu,8);cpu.execute(10)
 execute(cpu,[17,20,10,4]);cpu.execute(15,'M1_2');execute(cpu,[11,10,10,10]);cpu.ram[80]=0;cpu.execute(16,'M1_1');cpu.ram[0x34:0x36]=b'\x00\xdd';execute(cpu,[10]*5);checkpoint(0x24bc) #ED52 SBC HL,DE;22 LD(nn),HL.
 assert points[0x24bc]['foreground_tstates']-prefix['foreground_tstates']==17+world_map_cost(rom,room,flags)['foreground_tstates']
 return points
