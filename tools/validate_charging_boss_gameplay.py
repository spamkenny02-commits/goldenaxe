"""Deterministic pursuit/melee/charge segments through both production loops."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
TRIALS=[('appearance',0,80),('melee',10,49),('windup',14,27),('flight',18,20),('finish',18,17)]
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 for region in ['auto','pal']:
  for typ in [0x68,0x69]:
   for name,state,span in TRIALS:
    traces={}
    for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
     e=bytearray(768);e[0]=typ;e[1]=state;e[3]=0x40 if not state else 0x43;e[8]=0x6a;e[9]=0x9b;e[10]=1;e[12]=2;e[13]=20;e[0x11]=96;e[0x13]=128;e[0x18]=12 if typ==0x68 else 32;e[0x19]=4 if typ==0x68 else 8;e[0x1a]=2;e[0x25]=13
     if state==10:e[4]=8;e[8]=0xd6;e[13]=4
     if state==14:e[4]=26;e[8]=0xae;e[9]=0x9c;e[12]=e[13]=0
     if state==18:
      e[4]=32;e[8]=0xe8;e[9]=0x9c;e[13]=1;e[0x14:0x18]=bytes.fromhex('63feab00');e[0x21]=128
      if name=='finish':e[0x11]=55;e[0x25]=1
     base=0x600 if tag=='sms' else sy['world_actor_state'];writes=[(2800,base,e)]
     if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
     else:
      for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
     rows={}
     def observe(f,r):
      if not 2800<=f<2800+span:return
      rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
     with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/charging-boss-gameplay-{typ:02x}-{name}-{region}-{tag}',{2805,2820},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
     traces[tag]=rows
    for f in traces['sms']:
     a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,typ,name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
    if name=='finish':assert traces['md'][2800][1]==2 and traces['md'][2800][0x25]==13
    if name=='appearance':assert traces['md'][2879][1]==8 and traces['md'][2879][4]==0
    cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_exact=True))
    print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor/hero records injected in exterior. Production state, integration, animation/flash, collision publication and chase execute unchanged.','Segments stop before random attack/charge/rebound selection. Shared type68 charge states tested even though its normal choice branch only initiates melee. Natural room travel/combat, complete SAT/framebuffer/audio, inherited E degenerate expiry and hardware timing remain unproved.'])
 (ROOT/'validation/charging_boss_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
