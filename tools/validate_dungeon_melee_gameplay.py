"""Deterministic5F/60 melee segments production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for typ in [0x5f,0x60]:
  trials.append((typ,'appearance',2,30))
  for d in range(4):trials += [(typ,f'walk-{d}',6,16),(typ,f'continuation-{d}',12,16),(typ,f'attack-{d}',10,34)]
  if typ==0x60:
   trials += [(typ,'close',8,34),(typ,'chase',8,16),(typ,'wall',8,1)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48];v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=128;v[10]=int(name[-1]) if name.startswith(('walk-','continuation-','attack-')) else 1
    v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else 'd997' if state==10 else '4997');v[12]=4 if state in [2,10] else 2;v[13]=10 if state==2 else 11 if state==10 else 16
    if state==12:v[4]=16;v[0x14:0x18]=source[0x85da+v[10]*4:0x85de+v[10]*4]
    hx,hy=224,144;hxf=0;hc=0;hdx=0;tilemap=bytearray([32 if name=='wall' else 0]*1280)
    if name=='close':hx,hy=151,103
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-melee-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name.startswith('attack-'):assert traces['md'][2833][1]==4 and traces['md'][2833][10]==(int(name[-1])^1)
   if name=='close':assert traces['md'][2800][1]==10 and traces['md'][2833][1]==4
   if name=='chase':assert traces['md'][2800][1]==12 and traces['md'][2800][10]==3
   if name=='wall':assert traces['md'][2800][1]==4
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_and_hero_xy_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Both appearances stop before random heading selection. Four cardinal walks and pursuit-continuations, all four close attack animations through facing reversal/reset;60 deterministic close initiation, pursuit and blocked ground. Controlled tilemap/actor/hero fixtures, initial clocks aligned.5F random attack decisions and all spawn/random heading choices are tested in isolated cases only. Segments stop before subsequent random reads.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_melee_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
