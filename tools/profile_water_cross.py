"""Diagnose a controlled water departure through the complete transition."""
import contextlib,hashlib,io,json,re,sys,ctypes as ctypes
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 fast='--slow' not in sys.argv
 suffix='' if fast else '_slow'
 ground='--ground' in sys.argv
 kind='ground' if ground else 'water'
 scroll_cycles='--scroll-cycles' in sys.argv
 cycles='--cycles' in sys.argv or scroll_cycles
 core=ROOT.parents[1]/('work/genesis-plus-gx/genesis_plus_gx_scroll_libretro.dll' if scroll_cycles else 'work/genesis-plus-gx/genesis_plus_gx_clock_libretro.dll')
 dll=ctypes.CDLL(str(core));dll.gaw_timing_events.restype=ctypes.POINTER(ctypes.c_uint64);dll.gaw_timing_count.restype=ctypes.c_uint
 cases=[]
 for region,direction in [(r,d) for r in ['auto','pal'] for d in (range(4) if '--all' in sys.argv else [0] if '--up' in sys.argv else [1])]:
  x,y=[(128,48),(128,112),(48,80),(208,80)][direction]
  records={};patterns={};clock=[0];source_events=[];previous=[0]
  for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   items=bytearray(17);items[0]=items[4]=items[16]=1;items[14]=int(fast);water=bytes([0,0] if ground else [0x11,0xc0])*640
   writes=[(2800,0x600,bytes(768)),(2800,0xe0,items),(2800,0xdf,b'\x04'),(2800,0x30a,bytes([direction])),(2800,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(2800,0x1600,water)] if tag=='sms' else [(2800,sy['world_actor_state'],bytes(768)),(2800,sy['hero_items'],items),(2800,sy['hero_attack_speed'],int(fast).to_bytes(2,'big')),(2800,sy['hero_selected_item'],(4).to_bytes(2,'big')),(2800,sy['hero_direction'],direction.to_bytes(2,'big')),(2800,sy['hero_y'],(y<<8).to_bytes(2,'big')),(2800,sy['hero_x'],(x<<8).to_bytes(2,'big')),(2800,sy['sms_vram']+0x3800,water),(2800,sy['vtimer'],clock[0].to_bytes(4,'big'))]
   rows={};tiles={}
   def observe(f,r):
    if tag=='sms' and f==2799:
     clock[0]=r[0x2f]
     if cycles:dll.gaw_timing_reset();previous[0]=0
    if cycles and tag=='sms' and f>=2800:
     count=dll.gaw_timing_count();ptr=dll.gaw_timing_events()
     for n in range(previous[0],count):
      values=[int(ptr[n*8+j]) for j in range(8)]
      if values[0] in [0x1780,0x18ac,0x1d0d,0x18e1,0x18b7,0x24ed,0x24f2,0x20d3,0x190b,0x2260,0x24c5,0x21a1,0x2099,0x20ac,0x20f8,0x20fc,0x20ff,0x2113,0x2237,0x2081,0x2093,0x20c1,0x2c63,0x2c8d,0x1caf]:source_events.append([f]+values)
     previous[0]=count
    if not 2810<=f<=2960:return
    if tag=='sms':rows[f]=dict(state=r[0x1d],room=int.from_bytes(r[0xb9:0xbb],'little'),hero=list(r[0x310:0x318]),animation=r[0x30b],hero_state=r[0x301],hero_flags=r[0x303],hero_counter=r[0x304],context=r[0x41],cells=bytes(r[0x1c00:0x1ca0]).hex(),map=bytes(r[0x1600:0x1b00]).hex())
    else:
     def data(k,n):return bytes(r[(sy[k]+i)^1] for i in range(n))
     word=lambda k:int.from_bytes(data(k,2),'big')
     rows[f]=dict(state=word('game_state'),room=word('room_id'),hero=list(data('hero_y',2)[::-1]+data('hero_x',2)[::-1]+data('hero_dy',2)[::-1]+data('hero_dx',2)[::-1]),animation=word('hero_animation'),hero_state=word('hero_state'),hero_flags=word('hero_flags'),hero_counter=word('hero_counter'),context=word('hero_terrain_context'),cells=data('scratch',0x8a0)[0x800:0x8a0].hex(),map=data('sms_vram',0x3d00)[0x3800:0x3d00].hex(),stage=word('transition_stage'),step=word('transition_step'))
   def vram(f,v):
    if f in rows:
     tiles[f]=[sms_pixels(v,496+n) if tag=='sms' else md_pixels(v,512+n) for n in range(4)]
     sprites=[]
     if tag=='sms':
      for n in range(64):
       if v[0x3f00+n]==0xd0:break
       sprites.append([v[0x3f00+n],v[0x3f80+n*2],v[0x3f81+n*2]])
     else:
      word=lambda a:int.from_bytes(bytes([v[a^1],v[(a+1)^1]]),'big')
      n=0
      for count in range(80):
       a=0xf400+n*8;sprites.append([(word(a)-145)&255,(word(a+6)-128)&255,(word(a+4)&0x7ff)-272])
       n=word(a+2)&127
       if not n:break
     rows[f]['sprite_entries']=sprites
   with contextlib.redirect_stdout(io.StringIO()):run(rom,2960,ROOT/f'validation/{kind}-cross{suffix}-{region}-{direction}-{tag}',set(),([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+[(2808,2840 if fast else 2860,4+direction)],core=core if cycles and tag=='sms' else None,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
   for f,value in tiles.items():rows[f]['hero_pattern_sha256']=hashlib.sha256(json.dumps(value).encode()).hexdigest()
   records[tag]=rows;patterns[tag]=tiles
  changes={tag:{k:[f for f in rows if f>2810 and rows[f][k]!=rows[f-1][k]] for k in ['state','room','cells','map','context','animation']} for tag,rows in records.items()}
  differences={k:[f for f,a in records['sms'].items() if a[k]!=records['md'][f][k]] for k in records['sms'][2810]}
  pd=[f for f in patterns['sms'] if patterns['sms'][f]!=patterns['md'][f]]
  cases.append(dict(region=region,direction=direction,source_events=source_events,changes=changes,differences=differences,hero_pattern_difference_frames=pd,records=records))
  print(region,direction,changes,'differences',{k:v[:8] for k,v in differences.items()},'patterns',pd,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),diagnostic_only=True,controlled_all_water_software_map=not ground,controlled_all_ground_software_map=ground,fast_movement=fast,cases=cases)
 (ROOT/f'validation/{kind}_cross{suffix}{"_all" if "--all" in sys.argv else "_up" if "--up" in sys.argv else ""}{"_scroll_cycles" if scroll_cycles else "_cycles" if cycles else ""}_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
