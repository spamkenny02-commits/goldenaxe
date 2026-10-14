"""Deterministic5E floor triggers and77 edge-directed flights production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for origin in ['left','right','top','corner']:trials.append((0x5e,f'cycle-{origin}',2,105))
 for left,right in [(0,0),(0,1),(1,0),(1,1)]:trials.append((0x5e,f'floor-{left}{right}',2,4))
 trials += [(0x5e,'full-pool',4,51),(0x5e,'single-free-slot',4,51),(0x5e,'cache-crossing',2,3)]
 for origin in ['left','right','top','corner']:trials.append((0x77,f'flight-{origin}',0,100))
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);slot=8 if typ==0x77 else 0;v=memoryview(e)[slot*48:slot*48+48];v[0]=typ;v[1]=state;v[3]=0;v[0x11]=80;v[0x13]=32;v[10]=0
    if typ==0x5e:v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3];v[8:10]=bytes.fromhex('1597')
    if name.startswith(('cycle-','flight-')):v[0x13],v[0x11]={'left':(32,80),'right':(224,80),'top':(128,32),'corner':(32,32)}[name.split('-')[1]]
    if name in ['full-pool','single-free-slot']:
     for n in range(8,16):e[n*48]=0x5e;e[n*48+1]=6;e[n*48+4]=100
     if name=='single-free-slot':e[9*48:10*48]=bytes(48)
    hx,hy=224,144;hxf=0;hc=0;hdx=0;tilemap=bytearray(1280)
    if name.startswith('floor-'):
     off=(((hy-12)&248)*8)+(((hx-12)>>2)&62);tilemap[off+66]=int(name[-2]);tilemap[off+68]=int(name[-1])
    if name=='cache-crossing':
     hx,hy=235,80;hxf=255;hc=4;hdx=256;off=(((hy-12)&248)*8)+(((hx-12)>>2)&62);tilemap[off+66]=tilemap[off+68]=1
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e),(2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,tilemap)]
    if tag=='sms':writes += [(2800,0x301,b'\x01'),(2800,0x303,bytes([3,hc,0])),(2800,0x310,(hy<<8).to_bytes(2,'little')+((hx<<8)|hxf).to_bytes(2,'little')+bytes(2)+hdx.to_bytes(2,'little'))]
    else:
     for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',hc),('hero_hurt',0),('hero_y',hy<<8),('hero_x',(hx<<8)|hxf),('hero_dy',0),('hero_dx',hdx)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes(r[0x310:0x314])
      else:
       def w(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
       rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+w('hero_y').to_bytes(2,'little')+w('hero_x').to_bytes(2,'little')
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-floor-trap-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name.startswith('cycle-'):
    for f in [2801,2851,2901]:assert any(traces['md'][f][n*48]==0x77 and traces['md'][f][n*48+4]==127 for n in range(8,16)),(region,name,'birth at50-tick spacing',f)
   if name=='full-pool':assert all(traces['md'][2800][n*48]==0x5e for n in range(8,16)) and traces['md'][2850][1]==6
   if name=='single-free-slot':assert traces['md'][2800][9*48]==0x77 and traces['md'][2850][1]==6
   if name=='floor-11':assert traces['md'][2803][1]==2
   if name in ['floor-00','floor-01','floor-10']:assert traces['md'][2801][384]==0x77
   if name=='cache-crossing':assert [traces['md'][f][1] for f in [2800,2801,2802]]==[2,4,6] and traces['md'][2802][384]==0x77
   if typ==0x77:assert traces['md'][2800][384]==0x77 and traces['md'][2899][384]==0
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_and_hero_xy_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production raw pre-movement hero floor cache, four zero/nonzero combinations and235.FF-to236 movement crossing. Three actual77 births50 ticks apart for left/right/top/corner emitters, first-free allocation and full pool failure, custom boundary flight/removal. Controlled tilemap/actor/hero fixtures; source/native routines contain no random choices, initial clocks aligned for surrounding world processing.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_floor_trap_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
