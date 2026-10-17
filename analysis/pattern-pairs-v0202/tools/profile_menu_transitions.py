"""Read-only natural inventory entry/exit and start-menu sound observations."""
import contextlib,ctypes as c,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_menu_libretro.dll';dll=c.CDLL(str(core))
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);dll.gaw_timing_count.restype=c.c_uint
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  for name,route in [('exterior',PRESSES[:8]),('first_house',PRESSES[:11]+[(2950,2958,7),(3000,3020,4)]),('second_house',PRESSES[:11]+[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)])]:
   results={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    rows=[];ev=[];prev=[0]
    def data(r,k,n):return bytes(r[(sy[k]+i)^1] for i in range(n))
    def observe(f,r):
     if tag=='sms' and f==3299:dll.gaw_timing_reset();prev[0]=0
     if f<3300:return
     if tag=='sms':
      count=dll.gaw_timing_count();p=dll.gaw_timing_events()
      for n in range(prev[0],count):
       pc,cycles,irq,room,clock,hl,de,bc=[int(p[n*8+j]) for j in range(8)]
       if pc in [0x70f2,0x70f5,0x71d2,0x71db,0x71f9,0x71fc,0x7213,0x20f8,0x20ff,0x2113,0x229c,0x032a,0x0bfe,0x1de2,0x722a,0x7252]:ev.append(dict(frame=f,pc=pc,cycles=cycles,irq=irq,hl=hl,de=de,bc=bc))
      prev[0]=count
      rows.append(dict(frame=f,state=r[0x1d],map_head=r[0x1600:0x1608].hex(),music=r[0x1e65],sfx=r[0x1e08],effect_latch=r[0x1e0f],clock=r[0x2f]))
     else:rows.append(dict(frame=f,state=int.from_bytes(data(r,'game_state',2),'big'),map_head=data(r,'sms_vram',0x3808)[0x3800:].hex(),music=int.from_bytes(data(r,'sound_current_track',2),'big'),sfx=data(r,'sound_ram',0x190)[8],effect_latch=data(r,'sound_ram',0x190)[15],clock=(int.from_bytes(data(r,'vtimer',4),'big')-int.from_bytes(data(r,'world_clock_shift',4),'big'))&255))
    folder=ROOT/f'validation/menu-transition-{name}-{region}-{tag}'
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3470,folder,set(range(3348,3371))|set(range(3398,3441)),([(200,220,0)] if tag=='sms' else [])+route+[(3350,3355,0),(3400,3405,0)],ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region})
    results[tag]=dict(rows=rows,events=ev)
   cases.append(dict(name=name,region=region,results=results))
   print(name,region,'source relevant events',[(e['frame'],hex(e['pc'])) for e in results['sms']['events'] if 3348<=e['frame']<=3420],flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),production_roms_unmodified=True,ram_injections=False,cases=cases)
 (ROOT/'validation/menu_transition_profile.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
