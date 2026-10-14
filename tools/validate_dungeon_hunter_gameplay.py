"""Deterministic4F..51 pursuit/charge and projectile18 production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for typ in range(0x4f,0x52):trials += [(typ,'appearance',2,30),(typ,'walk',8,32)]
 trials.append((0x50,'full-charge',10,144))
 for d in range(4):trials.append((0x18,f'projectile-{d}',0,100))
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);slot=8 if typ==0x18 else 0;v=memoryview(e)[slot*48:slot*48+48]
    v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=64 if name=='full-charge' else 128;v[10]=3 if name=='full-charge' else 1
    if typ>=0x20:v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else 'b592');v[12]=4 if state==2 else 2;v[13]=10;v[0x2c]=16
    if state==8:v[4]=32;v[0x14:0x18]=source[0x87d2:0x87d6]
    if typ==0x18:v[3]=v[12]=v[13]=0;v[8:10]=bytes(2);v[10]=int(name[-1])
    hx,hy=224,144;writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if name=='full-charge':writes.append((2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,bytes(1280)))
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-hunter-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='full-charge':assert traces['md'][2943][1]==4 and traces['md'][2943][0x2c]==0
   if typ==0x18:assert traces['md'][2800][384]==0x18 and traces['md'][2899][384]==0
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, animation, walking, full16-segment50 charge and all four18 projectile flights/removal execute unchanged. Charge uses a controlled zero collision map and stops at state4 before random selection. Initial pursuit/shoot random choices are direct-routine checks.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_hunter_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
