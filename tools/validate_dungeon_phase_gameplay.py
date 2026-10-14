"""Deterministic46..49 production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x46,'far',2,48),(0x46,'near-wait',2,25),(0x46,'jump-flight',8,34),(0x14,'aimed-flight',0,100)]
 for typ in [0x47,0x48,0x49]:trials += [(typ,'appearance',2,30),(typ,'slow-pause',8,50),(typ,'walk',6,7)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=typ;e[1]=state;e[3]=3;e[0x11]=80;e[0x13]=128;e[10]=1;e[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    e[8:10]=bytes.fromhex('c291' if typ==0x46 else 'fa84' if state==2 else '2792');e[12]=0 if typ==0x46 else 4 if state==2 else 2;e[13]=0 if typ==0x46 else 10 if state==2 else 9
    if typ==0x14:e[3]=e[12]=e[13]=0;e[8:10]=bytes(2);e[0x18:0x1b]=bytes(3)
    if typ==0x46:e[11]=2;e[0x2e:0x30]=bytes.fromhex('e0ff')
    if name=='jump-flight':
     e[8:10]=bytes.fromhex('fd91');e[11]=0;e[12]=2;e[13]=14;e[0x22:0x24]=(128<<8).to_bytes(2,'little');e[0x26:0x28]=(80<<8).to_bytes(2,'little');e[0x20:0x22]=(128).to_bytes(2,'little');e[0x24:0x26]=(128).to_bytes(2,'little');e[0x28:0x2a]=(528).to_bytes(2,'little');e[0x2a:0x2c]=(512).to_bytes(2,'little');e[0x11]=78
    if state==8 and typ!=0x46:e[0x2f]=1
    if state==6:
     v=source[0x4f1c:0x4f21];e[4]=8;e[0x14:0x18]=v[:4];e[10]=v[4];e[0x2e]=20;e[13]=4
    hx,hy=(150,100) if name=='near-wait' else (224,144)
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-phase-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='near-wait':assert traces['md'][2824][1]==6
   if name=='jump-flight':assert traces['md'][2833][1]==6 and not int.from_bytes(traces['md'][2833][0x2a:0x2c],'little')
   if name=='aimed-flight':assert traces['md'][2800][1]==2 and traces['md'][2899][0]==0
   if typ==0x49 and name=='slow-pause':assert any(r[384]==0x14 for r in traces['md'].values()),'No projectile birth'
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, timers, integration, animation, collisions and projectile allocation execute unchanged. Stops before random movement/jump choices.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_phase_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
