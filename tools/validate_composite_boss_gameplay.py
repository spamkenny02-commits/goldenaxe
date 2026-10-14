"""Composite boss/phantom coordination in unmodified production game loops."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
TRIALS=[('appearance',0,170),('idle',8,90),('hit',8,22),('death',8,90),('fade',8,90)]
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  for name,state,span in TRIALS:
   traces={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=0x67;e[1]=state;e[3]=0x40 if not state else 0x42;e[8]=0x62 if not state else 0x98;e[9]=0x9a;e[12]=2;e[13]=16;e[0x11]=88;e[0x13]=128;e[0x18]=1 if name=='death' else 60;e[0x19]=18;e[0x1a]=2
    if state:
     for n in range(1,6):
      p=n*48;e[p]=0x67;e[p+1]=22 if name=='fade' else 20;e[p+3]=1 if name=='fade' else 3;e[p+4]=48 if name=='fade' else 128;e[p+8]=0x34;e[p+9]=0x9b;e[p+12]=2;e[p+13]=8;e[p+0x11]=56;e[p+0x13]=48+n*24
    base=0x600 if tag=='sms' else sy['world_actor_state'];writes=[(2800,base,e)]
    if name in ['hit','death']:writes += [(2810,base+0x1d,b'\x01')]
    if name=='death':
     pool=bytearray(384)
     for n in range(8):pool[n*48]=1;pool[n*48+1]=2;pool[n*48+6]=255
     writes += [(2812,base+384,pool)]
    if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if not 2800<=f<2800+span:return
     rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/composite-boss-gameplay-{name}-{region}-{tag}',{2815,2850},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=sorted(writes,key=lambda w:w[0]),ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   random_timer_differences=0
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    differences=[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y]
    allowed={n*48+4 for n in range(1,6) if name=='appearance' and a[n*48+1]==b[n*48+1]==20}
    assert all(j in allowed for j,x,y in differences),(region,name,f,differences[:24])
    random_timer_differences+=len(differences)
    if name=='appearance':
     for tag in ['sms','md']:
      current=traces[tag][f]
      for n in range(1,6):
       p=n*48
       if current[p+1]!=20:continue
       previous=traces[tag][f-1]
       if previous[p+1]==18:assert 112<=current[p+4]<=127
       else:assert current[p+4]==previous[p+4]-1
   if name=='death':assert all(not traces['md'][2889][n*48] for n in range(1,6)) and traces['md'][2889][0]==7
   if name=='fade':assert all(not traces['md'][2889][n*48] for n in range(1,6))
   if name=='hit':
    assert traces['md'][2810][1]==10 and traces['md'][2810][0x18]==59
    assert traces['md'][2821][1]==14 and all(traces['md'][2821][n*48+1]==22 for n in range(1,6))
   if name=='appearance':
    assert traces['md'][2969][1]==6 and all(traces['md'][2969][n*48+1]==20 for n in range(1,6))
   cases.append(dict(region=region,segment=name,frames=span,all_768_actor_bytes_exact=not random_timer_differences,random_appartition_timer_differences=random_timer_differences,all_other_actor_bytes_exact=True,random_timer_initial_bounds_and_individual_decrements_checked=name=='appearance'))
   print(region,name,span,'actor frames checked; random timer differences:',random_timer_differences,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled core/phantom records and hero position injected in exterior. Hit/death scenarios inject pending damage. Death scenario occupies eight transient slots after initial boss-death clear to suppress divergent random particles.','Appearance compares all bytes except random state20 phantom counters; their initial 112..127 bounds and subsequent individual decrements are checked. These counters can differ because original refresh values are not reproduced. Other scenarios compare all 768 bytes.','Production behavior, spawning, delays, animation, hurt, coordination and removal execute. Segments stop before random formation/position/shot choices. Natural dungeon combat, SAT/framebuffer/audio and hardware timing remain unproved.'])
 (ROOT/'validation/composite_boss_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
