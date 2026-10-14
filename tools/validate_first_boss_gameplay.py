"""Compare first-boss deterministic movement/attack segments in both game loops."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  for state,span in [(0,90),(8,32),(10,32)]:
   traces={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=0x64;e[1]=state;e[2]=0;e[3]=0x40 if state==0 else 0x43;e[4]=1;e[8]=0x13;e[9]=0x99;e[10]=1;e[12]=2;e[13]=40;e[0x11]=96;e[0x13]=128;e[0x18]=60;e[0x19]=20;e[0x1a]=4;e[0x20]=5
    # Controlled exterior segment isolates AI from room scripts and loading.
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if not 2800<=f<2800+span:return
     rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    folder=ROOT/f'validation/first-boss-gameplay-{state}-{region}-{tag}'
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,folder,{2805,2820},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    assert a==b,(region,state,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   cases.append(dict(region=region,seed_state=state,frames=span,all_768_actor_bytes_exact=True))
   print(region,state,span,'actor frames exact',flush=True)
 result=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled boss record and hero position injected in exterior; production actor loop, movement integration, animation, projectiles and culling execute unchanged.','Segments stop before random attack selection. Natural fight, original random stream, dungeon loading/graphics, complete framebuffer and audio not established.'])
 (ROOT/'validation/first_boss_gameplay_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
