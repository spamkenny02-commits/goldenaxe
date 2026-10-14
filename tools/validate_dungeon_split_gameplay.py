"""Deterministic4A/4B production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for typ in [0x4a,0x4b]:trials += [(typ,'appearance',2,30),(typ,'move',6,15),(typ,'pause',8,31),(typ,'surviving-hit',8,1),(typ,'lethal-hit',8,1)]
 trials += [(0x4b,'split',8,32),(0x4b,'split-earlier-slot',8,32)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);slot=4 if name=='split-earlier-slot' else 0;v=memoryview(e)[slot*48:slot*48+48]
    if name=='split-earlier-slot':
     for n in range(16):
      if n in [1,4,5,12]:continue
      w=memoryview(e)[n*48:n*48+48];w[0]=0x46;w[1]=2;w[8:10]=bytes.fromhex('c291');w[11]=2;w[0x11]=w[0x13]=8
    v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=128;v[10]=1;v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else '5192');v[12]=4 if state==2 else 2;v[13]=10 if state==2 else 5;v[0x20]=typ==0x4b
    if state==6:v[4]=16;v[0x14:0x18]=source[0x9b12:0x9b16]
    if state==8:v[4]=32
    if name=='lethal-hit':v[0x1d]=v[0x18]
    elif name=='surviving-hit' or name.startswith('split'):v[0x1d]=1
    v[0x1e:0x20]=bytes.fromhex('00c3');hx,hy=224,144
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,value in [('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-split-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name.startswith('split'):
    assert sum(r[0]==0x4b for r in [traces['md'][2800][n*48:n*48+48] for n in range(16)])==4
    assert all(traces['md'][2800+span-1][n*48+0x20]==0 for n in range(16) if traces['md'][2800+span-1][n*48]==0x4b)
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, timers, integration, animation, damage and split allocation execute unchanged. Earlier-slot clone layout retains unprocessed copied damage until the next frame. Stops before random choices.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_split_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
