"""Controlled exits through the production SMS/MD game loops and room loaders."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 path=[(3,241,112),(0,128,15),(3,241,80),(1,128,161),(0,128,15),(1,128,161)]
 reports=[]
 for region in ['auto','pal']:
  records={}
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   writes=[];presses=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8];rows={}
   def add(f,k,v,n=2):writes.append((f,sy[k],v.to_bytes(n,'big')))
   for i,(d,x,y) in enumerate(path):
    f=2800+i*400;presses.append((f,f+3,4+d))
    if tag=='sms':
     writes += [(f,0x600,bytes(768)),(f,0xa2,b'\0'),(f,0x301,b'\0'),(f,0x303,b'\x03\0'),(f,0x30a,bytes([d])),(f,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')+bytes(4)),(f,0x1600,bytes(1280))]
     if i==0:writes += [(f,0xb9,b'\x77\0'),(f,0x6c,b'\0'),(f,0x40,b'\0')]
    else:
     writes += [(f,sy['world_actor_state'],bytes(768)),(f,sy['sms_vram']+0x3800,bytes(1280))]
     for k,v in [('world_actor_count',0),('hero_state',0),('hero_flags',3),('hero_counter',0),('hero_direction',d),('hero_y',y<<8),('hero_x',x<<8),('hero_dy',0),('hero_dx',0)]:add(f,k,v)
     if i==0:
      add(f,'room_id',0x77);add(f,'world_graphics_class',0);add(f,'forest_maze_progress',0,1)
   def observe(f,r):
    if f not in [3100+i*400 for i in range(6)]:return
    if tag=='sms':rows[f]=dict(state=r[0x1d],room=int.from_bytes(r[0xb9:0xbb],'little'),progress=r[0x6c],cells=bytes(r[0x1c00:0x1ca0]).hex(),map=bytes(r[0x1600:0x1b00]).hex())
    else:
     def data(k,n,offset=0):return bytes(r[(sy[k]+offset+i)^1] for i in range(n))
     def w(k):return int.from_bytes(data(k,2),'big')
     rows[f]=dict(state=w('game_state'),room=w('room_id'),progress=data('forest_maze_progress',1)[0],cells=data('scratch',160,0x800).hex(),map=data('sms_vram',1280,0x3800).hex())
   with contextlib.redirect_stdout(io.StringIO()):run(rom,5100,ROOT/f'validation/forest-maze-live-{region}-{tag}',set(),presses,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   records[tag]=rows
  for i,f in enumerate([3100+j*400 for j in range(6)]):
   a,b=records['sms'][f],records['md'][f]
   assert a==b,(region,i,{k:(a[k],b[k]) for k in a if a[k]!=b[k]})
   assert (a['state'],a['room'],a['progress'])==(12,0x77 if i!=4 else 0x67,i+1 if i<5 else 0),(region,i,a)
  reports.append(dict(region=region,source_and_native_settled_states_cells_maps_exact=True,records=records))
  print(region,'six production exits and settled room maps exact',flush=True)
 result=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=reports,full_game_ported=False,limits=['Controlled relocation to maze, six boundary positions, cleared enemies and temporary all-ground departure maps. Original and native production game loops and destination room loaders execute normally.','Settled state, room, maze stage, 160 metatiles and 1280 software map bytes compared after every exit. Natural travel to the maze, exact transition frames, framebuffers and audio remain outside this test.'])
 (ROOT/'validation/forest_maze_gameplay_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
