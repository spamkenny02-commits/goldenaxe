"""Deterministic56/59/5A teleport cycles and17/71 projectiles production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x56,'full-visible-cycle',2,96),(0x59,'flash-reveal',2,36),(0x5a,'flash-reveal',2,36),(0x59,'disappear',6,32),(0x5a,'disappear',6,24)]
 for typ in [0x59,0x5a]:
  for d in range(4):trials.append((typ,f'shot-{d}',4,12))
 for typ in [0x17,0x71]:
  for d in range(4):trials.append((typ,f'projectile-{d}',0,100))
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);slot=8 if typ in [0x17,0x71] else 0;v=memoryview(e)[slot*48:slot*48+48]
    v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=128;v[10]=int(name[-1]) if name.startswith('shot-') else 1
    if typ not in [0x17,0x71]:v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('d794' if typ==0x56 else 'aa95' if state==2 else 'f695');v[12]=v[13]=0
    if state==2:v[3]&=253;v[5]=32;v[4]=32 if typ==0x56 else 0
    if state==4:v[4]=8
    if state==6:v[4]=16
    if typ in [0x17,0x71]:v[3]=v[12]=v[13]=0;v[8:10]=bytes(2);v[10]=int(name[-1])
    hx,hy=224,144
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
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-teleport-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   masked=[]
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    random_timer=(name=='flash-reveal' and a[1]==b[1]==4) or (name.startswith('shot-') and a[1]==b[1]==6)
    if random_timer:
     lo,hi=(35,47) if name=='flash-reveal' else (19,27)
     assert lo<=a[4]<=hi and lo<=b[4]<=hi,(region,name,f,a[4],b[4]);masked.append(f)
     a=a[:4]+a[5:];b=b[:4]+b[5:]
    assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='full-visible-cycle':assert traces['md'][2832][1]==4 and traces['md'][2864][1]==6 and traces['md'][2864][384]==0x71 and traces['md'][2880][1]==8
   if name=='flash-reveal':assert traces['md'][2835][1]==4
   if name.startswith('shot-'):assert traces['md'][2808][1]==6 and traces['md'][2808][384]==0x17
   if name=='disappear':assert traces['md'][2816][1]==8 and traces['md'][2816][4]==(7 if typ==0x5a else 15)
   if typ in [0x17,0x71]:assert traces['md'][2800][384]==typ and traces['md'][2899][384]==0
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=not masked,excluded_random_record_offsets=[4] if masked else [],excluded_random_frames=masked,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames compared',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production56 full visible cycle from flash32 through live contact, actual71 allocation, wait16 and fade16;59/5A reveal, normal17 allocation in all four directions, and unequal16/8 fades. All17/71 trajectories/removal.','Only parent timer4 after random reveal/shoot delay is excluded for recorded frames; all other768 actor bytes are compared. Original random outputs are covered in the isolated tests. Segments stop before next uncontrolled respawn/cooldown.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_teleport_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
