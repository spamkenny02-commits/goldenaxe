"""Deterministic54/55 telegraphs and projectile71 production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for typ in [0x54,0x55]:trials += [(typ,'appearance',2,40),(typ,'idle',6,80)]
 for d in range(4):trials.append((0x55,f'aligned-{d}',6,15))
 trials += [(0x54,'repeat-telegraph',8,127),(0x55,'telegraph',8,15)]
 for d in range(4):trials.append((0x71,f'projectile-{d}',0,100))
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);slot=8 if typ==0x71 else 0;v=memoryview(e)[slot*48:slot*48+48]
    v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=128;v[10]=1
    if typ!=0x71:v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else 'd794' if state==8 else '8b94');v[12]=4 if state==2 else 2 if state==8 else 0;v[13]=10 if state==2 else 8 if state==8 else 0
    if state==6:v[4]=128 if name.startswith('aligned') else 96
    if state==8:v[4]=128 if typ==0x54 else 8
    if typ==0x71:v[3]=v[12]=v[13]=0;v[8:10]=bytes(2);v[10]=int(name[-1])
    hx,hy=224,144
    if name.startswith('aligned'):hx,hy=[(128,32),(128,144),(32,80),(224,80)][int(name[-1])]
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-emitter-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    if name=='appearance' and a[1]==b[1]==6:
     # The only source/native difference is the unaligned random cooldown.
     assert 100<=a[4]<=128 and 100<=b[4]<=128,(region,name,f,a[4],b[4])
     a=a[:4]+a[5:];b=b[:4]+b[5:]
    assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='appearance':assert traces['md'][2839][1]==6
   if name.startswith('aligned'):assert traces['md'][2800][1]==8 and traces['md'][2808][1]==10 and traces['md'][2800][10]==int(name[-1])
   if typ==0x71:assert traces['md'][2800][384]==0x71 and traces['md'][2899][384]==0
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=name!='appearance',excluded_random_offsets=[4] if name=='appearance' else [],clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop and animation: both full appearances (only random cooldown byte4 excluded after reset), idle and four aligned55 attacks despite nonzero timer, repeat telegraph54, telegraph55, all four71 flights/removal. Random shot/repeat decisions are covered in the isolated tests, not the production segments, which stop before those reads.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_emitter_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
