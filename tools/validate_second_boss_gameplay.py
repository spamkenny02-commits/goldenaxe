"""Compare deterministic core/satellite segments in unmodified game loops."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
TRIALS=[('appearance',0,0,0,49),('orbit8',8,8,0,90),('orbit3',8,3,128,90),('vulnerable',8,0,192,90),('movement',6,8,64,32),('destroy-shield',8,8,0,90)]
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  for name,state,count,phase,span in TRIALS:
   traces={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=0x65;e[1]=state;e[3]=0x40 if not state else 0x41;e[8]=2;e[9]=0x9a;e[12]=e[13]=2 if state else 0;e[0x11]=80;e[0x13]=128;e[0x18]=72;e[0x19]=12;e[0x1a]=2;e[0x28]=16;e[0x29]=phase;e[0x2b]=count;e[0x2e]=20;e[0x2f]=120
    if state==6:e[4]=32;e[0x14:0x18]=bytes.fromhex('80ff8000');e[10]=3
    for n in range(count):e[(8+n)*48]=0x66
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if name=='destroy-shield':
     base=0x600 if tag=='sms' else sy['world_actor_state']
     for n in range(8,16):writes += [(2805,base+n*48+6,b'\x01'),(2805,base+n*48+0x1d,b'\x0c')]
    if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if not 2800<=f<2800+span:return
     rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    folder=ROOT/f'validation/second-boss-gameplay-{name}-{region}-{tag}'
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,folder,{2805,2820},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    assert a==b,(region,name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name=='destroy-shield':
    r=traces['md'];assert all(r[2805][n*48]==1 for n in range(8,16))
    assert r[2805][3]&2==0
    assert r[2889][0x2b]==0 and r[2889][3]&2
   cases.append(dict(region=region,segment=name,seed_state=state,satellites=count,frames=span,all_768_actor_bytes_exact=True))
   print(region,name,span,'actor frames exact',flush=True)
 result=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled boss records/hero position in exterior. Shield destruction injects pending lethal damage and one freeze tick into each satellite, then production death particles and vulnerability execute. Loot random outcomes are not compared.','Segments stop before random movement selection; natural combat/dungeon loading, framebuffer/SAT, audio and exact hardware timing are not proved.'])
 (ROOT/'validation/second_boss_gameplay_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
