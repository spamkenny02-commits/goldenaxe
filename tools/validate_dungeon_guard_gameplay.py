"""Deterministic5C/5D movement and normal-button directional weapon hits production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[]
 for typ in [0x5c,0x5d]:
  trials.append((typ,'appearance',2,30))
  for d in range(4):trials += [(typ,f'walk-{d}',6,16),(typ,f'continuation-{d}',10,16)]
  for hd in range(4):
   for mode in ['allowed','blocked']:trials.append((typ,f'weapon-{mode}-{hd}',8,32))
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48];v[0]=typ;v[1]=state;v[3]=0x23;v[0x11]=80;v[0x13]=128;v[10]=int(name[-1]) if name.startswith(('walk-','continuation-')) else 1
    v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else '8596');v[12]=4 if state==2 else 2;v[13]=10
    hd=1;hx,hy=224,144;presses=[]
    if name.startswith('continuation-'):v[4]=16;v[0x14:0x18]=source[0x85da+v[10]*4:0x85de+v[10]*4]
    if name.startswith('weapon-'):
     hd=int(name[-1]);hx,hy=[(128,96),(128,64),(144,80),(112,80)][hd];v[10]=hd^1 if '-allowed-' in name else hd;v[4]=64;presses=[(2802,2804,8)]
    if state!=2:
     def word(a):return int.from_bytes(source[0x30000+(a&0x3fff):0x30002+(a&0x3fff)],'little')
     address=word(word(0x9685+v[10]*2));start=0x30000+(address&0x3fff);v[0x1b:0x1d]=source[start+1:start+3]
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e),(2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,bytes(1280))]
    if tag=='sms':writes += [(2800,0x301,b'\x01'),(2800,0x303,b'\x03\0\0'),(2800,0x30a,bytes([hd,0])),(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',0),('hero_hurt',0),('hero_animation',0),('hero_direction',hd),('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes([r[0x301],r[0x30a],r[0x30b],r[0x318],r[0x1e08]])
      else:
       def w(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
       rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+bytes([w('hero_state'),w('hero_direction'),w('hero_animation'),w('hero_health'),w('sound_effect_request')])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-guard-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+presses,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name.startswith('weapon-'):
    hp=source[0x320ea+(typ-32)*4];final=traces['md'][2831][0x18]
    assert final<hp if '-allowed-' in name else final==hp,(region,name,hp,final)
    assert traces['md'][2831][771]==24,(region,name,'hero hurt during isolated attack')
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_hero_state_facing_animation_hp_and_sound_request_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, animation and cardinal half-pixel16-tick movement; normal C-button primary-weapon attacks from all four sides prove each opposing enemy facing accepts damage and same facing rejects it, including HP/hurt/sound pipeline. Controlled zero collision map; waiting actors counter64 and zero velocity isolate attacks before random decisions. Conditional5C/5D decisions and post-AI facing gate are covered in isolated cases.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_guard_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
