"""Deterministic57/58 sentinel activation/movement/park production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x57,'hidden',2,48),(0x58,'hidden',2,48),(0x57,'activation-contact-walk',2,49),(0x58,'activation',2,32),(0x58,'park-resume',12,129)]
 for typ in [0x57,0x58]:
  for d in range(4):trials += [(typ,f'walk-{d}',6,16),(typ,f'fast-{d}',10,8)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48]
    v[0]=typ;v[1]=state;v[3]=0x28 if state==2 else 0x2b;v[0x11]=80;v[0x13]=128;v[10]=int(name[-1]) if name.startswith(('walk-','fast-')) else 1
    v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('9195' if state==12 else '6795');v[12]=0 if state==12 else 2;v[13]=12
    if state==12:v[4]=128;v[14]=3
    if name.startswith('fast-'):v[4]=8;v[0x14:0x18]=source[0x85eb+v[10]*4:0x85ef+v[10]*4]
    hx,hy=(128,80) if name.startswith('activation') else (224,144)
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e),(2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,bytes(1280))]
    if tag=='sms':writes += [(2800,0x301,b'\x01'),(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,value in [('hero_state',1),('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes([r[0x318]])
      else:rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+bytes([int.from_bytes(bytes(r[(sy['hero_health']+i)^1] for i in range(2)),'big')])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-sentinel-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='hidden':assert traces['md'][2800+span-1][1]==2 and traces['md'][2800+span-1][3]&3==0
   if name=='activation-contact-walk':assert traces['md'][2832][1]==6 and traces['md'][2848][768]<24
   if name=='activation':assert traces['md'][2831][1]==10 and traces['md'][2831][4]==0
   if name=='park-resume':assert traces['md'][2928][1]==4 and traces['md'][2928][12]==2
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_and_hero_hp_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, animation and hero damage. Hidden waiting,32-tick activation,57 contact and first16-tick walk,58 full128-tick park/resume, four16-tick half-pixel walks and four8-tick one-pixel fast moves for each type. Controlled zero collision map. Segments stop before uncontrolled random selection; conditional pursuit/58 parking decisions covered by isolated original-routine execution.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_sentinel_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
