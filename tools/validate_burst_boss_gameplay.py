"""Full deterministic first burst/disappearance cycle in production loops."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 source=(ROOT/'input/original.sms').read_bytes();cases=[]
 for region in ['auto','pal']:
  for typ in [0x6a,0x6b]:
   traces={};source_clock=[];clock_adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);e[0]=typ;stats=source[0x320ea+(typ-32)*4:0x320ea+(typ-31)*4];e[0x18:0x1b]=stats[:3];e[3]=stats[3]
    base=0x600 if tag=='sms' else sy['world_actor_state'];writes=[(2800,base,e)]
    if tag=='sms':writes += [(2800,0x310,(144<<8).to_bytes(2,'little')+(224<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,v in [('hero_y',144<<8),('hero_x',224<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],v.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big')
       shift=read32('world_clock_shift');clock=(read32('vtimer')-shift)&255
       adjustment=clock-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')))
       clock_adjustments.append(adjustment)
     if not 2800<=f<3052:return
     rows[f]=bytes(r[0x600:0x900]) if tag=='sms' else bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,3052,ROOT/f'validation/burst-boss-gameplay-{typ:02x}-{region}-{tag}',{2848,2915,2945,3000},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,typ,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   r=traces['md'];assert all(r[2908][n*48]==0x74 for n in range(8,16))
   assert r[2988][1]==14 and all(not r[3051][n*48] for n in range(8,16))
   if typ==0x6a:assert any(r[2944][n*48+1]==8 for n in range(8,16))
   else:assert any(r[2944][n*48+1]==6 for n in range(8,16))
   cases.append(dict(region=region,type=typ,frames=252,all_768_actor_bytes_exact=True,clock_adjustments=clock_adjustments,first_eight_shot_burst_and_variant_branch_and_clear_verified=True))
   print(region,hex(typ),'252 frames: first burst, variant and disappearance exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled boss/hero records injected in exterior, initial stats from original; MD world clock explicitly aligned to source at fixture start. Production actor loop, animation-period-zero behavior, eight allocations, projectile flight/pause/variant branch, flash/cull and boss disappearance execute unchanged.','Without clock alignment NTSC type6B diverges at2977: MD projectile contact/removal is one frame earlier than SMS2978. This actual global-phase difference remains unresolved; this check isolates actor logic and does not prove absolute combat timing.','Stops before relocation random choices; natural dungeon fight, global clock/RNG, complete sprite/framebuffer/audio and hardware timing remain unproved.'])
 (ROOT/'validation/burst_boss_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
