"""Deterministic5B grab/gold theft/escape and hero immobilization production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x5b,'appearance',2,30),(0x5b,'walk',6,32),(0x5b,'capture-steal',10,65),(0x5b,'empty-wallet',12,33),(0x5b,'held-direction',12,33),(0x5b,'six-press-escape',12,31)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[];visible={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48];v[0]=typ;v[1]=state;v[3]=0x2b;v[0x11]=88 if state==12 else 80;v[0x13]=128;v[10]=1
    v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else '6c96' if state==12 else '4296');v[12]=4 if state==2 else 0 if state==12 else 2;v[13]=0 if state==12 else 10;v[0x21]=16
    if state==10:v[4]=32
    hx,hy=(128,80) if state in [10,12] else (224,144);hs=12 if state==12 else 1;gold=0 if name=='empty-wallet' else 32
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e),(2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,bytes(1280))]
    if tag=='sms':writes += [(2800,0xdd,bytes([gold])),(2800,0x301,bytes([hs])),(2800,0x303,b'\x03\0\0'),(2800,0x30b,b'\0'),(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,value in [('hero_state',hs),('hero_flags',3),('hero_counter',0),('hero_hurt',0),('hero_animation',0),('hero_gold',gold),('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    presses=[]
    if name=='held-direction':presses=[(2805,2825,7)]
    if name=='six-press-escape':presses=[(2810+i*4,2810+i*4,4 if i%2==0 else 7) for i in range(6)]
    rows={};hud={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes([r[0x301],r[0x304],r[0x30b],r[0x318],r[0xdd],r[0x1e08],r[0x1e05]])+bytes(r[0x310:0x318])
      else:
       def w(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
       rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+bytes([w('hero_state'),w('hero_counter'),w('hero_animation'),w('hero_health'),w('hero_gold'),w('sound_effect_request'),r[(sy['sound_ram']+5)^1]])+b''.join(w(k).to_bytes(2,'little') for k in ['hero_y','hero_x','hero_dy','hero_dx'])
    def vram(f,v):
     if not 2800<=f<2800+span:return
     if tag=='sms':hud[f]=[int.from_bytes(v[0x3dd0+n*2:0x3dd2+n*2],'little')&511 for n in range(3)]
     else:hud[f]=[(int.from_bytes(v[0xec90+n*2:0xec92+n*2],'little')&2047)-16 for n in range(3)]
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-thief-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+presses,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows;visible[tag]=hud
   assert visible['sms']==visible['md'],(region,name,'actual gold HUD tiles',visible)
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f]
    if name=='six-press-escape' and f==2830:
     # Escape immediately chooses a new random direction, not yet aligned.
     for row in [a,b]:assert row[1] in [4,8] and row[8:10]==bytes.fromhex('4296') and row[0x20:0x22]==bytes([0,16]) and row[768]==0
     assert a[768:]==b[768:],(region,name,f,'escape hero side effects',a[768:],b[768:])
     continue
    assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   last=traces['md'][2800+span-1]
   if name=='capture-steal':assert last[768]==12 and last[772]==28
   if name=='empty-wallet':assert last[772]==0
   if name=='held-direction':assert last[0x20]==1 and last[768]==12
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_and_hero_state_gold_xy_sound_exact_except_escape_random_actor_fields=True,actual_gold_hud_tiles_exact_each_frame=span,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, hero12 immobilization, capture-to-attachment same-frame fallthrough,65-frame capture/gold drain, empty funds, held direction counting once and six distinct directional press escape. Actual gold HUD tiles compare each frame, along with queued95/effect state. Controlled zero collision map. Escape tick chooses a new random actor direction: only its hero side effects and restored actor state/descriptor/counters compare; prior frames compare all768 actor bytes.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_thief_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
