"""Controlled type6C production sequences with explicit clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
TRIALS=[('appearance',0,65),('pursuit',4,32),('two-shots',10,120),('surviving-hit',10,1),('lethal-hit',10,1)]
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=list(TRIALS)
 for variant in range(4):
  lengths=[]
  for branch in range(4):
   address=int.from_bytes(source[0x4745+variant*8+branch*2:0x4747+variant*8+branch*2],'little')
   lengths.append(next(n for n in range(8) if source[address+n*2]==255))
  trials.append((f'path-{variant}',18,max(112,max(lengths)*24)+3))
 for region in ['auto','pal']:
  for name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=0x6c;e[1]=state;e[3]=0x40 if not state else 0x43;e[0x11]=72;e[0x13]=128;e[10]=1;e[8]=0x28;e[9]=0x9e;e[13]=16;e[12]=4
    e[0x18:0x1b]=source[0x320ea+(0x6c-32)*4:0x320ea+(0x6c-32)*4+3]
    if state==10:e[4]=32;e[8]=0xe3;e[13]=e[12]=0
    if name.endswith('-hit'):e[0x1d]=90 if name=='lethal-hit' else 8
    if state==18:
     e[4]=112;e[8]=0x14;e[9]=0xa0;e[12]=e[13]=0
     for n in range(4):
      e[(8+n)*48]=0x76;e[(8+n)*48+0x20]=int(name[-1]);e[(8+n)*48+0x21]=3-n
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big')
       shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/sword-boss-gameplay-{name}-{region}-{tag}',{2805,2820,2855,2909,2940},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   r=traces['md']
   if name=='two-shots':assert r[2854][384]==0x75 and r[2908][1]==2 and r[2908][4]==63
   if name=='surviving-hit':assert r[2800][0x18]==82 and r[2800][5]==32
   if name=='lethal-hit':assert r[2800][0]==7 and r[2800][1]==0 and r[2800][0x18]==0
   if name.startswith('path-'):assert all(not r[2800+span-1][n*48] for n in range(8,16)) and r[2800+span-1][1] in [4,8]
   cases.append(dict(region=region,segment=name,frames=span,all_768_actor_bytes_exact=True,clock_adjustments=adjustments))
   print(region,name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled boss and hero records injected into exterior. Native clock explicitly aligned to source in fixture; production code unchanged. Segments stop before random decisions.','Appearance, pursuit and two shots compared; four satellite formations injected with explicit path selection to isolate complete path/lifetime logic. Initial random state16 allocation is covered by direct routine tests. Type6C normal choices do not reach satellite states16/18. Natural fights/routes, global clock/RNG, full framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/sword_boss_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
