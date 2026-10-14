"""Source-core checks for2C rest,2E/2F emergence and projectile14."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(t,state,d=0,pose=0,timer=0):
  e=bytearray(48);e[0]=t;e[1]=state;e[2]=6;e[3]=0x28;e[4]=timer;e[8:10]=bytes.fromhex('8087' if t==0x2c else 'dc87');e[10]=d;e[11]=pose;e[12]=5;e[13]=12;e[0x11]=80;e[0x13]=120;e[0x18]=32
  return e
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-emerging-{name}';b=ROOT/f'validation/md-emerging-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 cases=[record(0x2c,s,d,timer=timer) for s,timer in [(6,0),(8,3),(10,0),(10,3)] for d in range(4)]
 cases +=[record(t,s,pose=p,timer=c) for t in [0x2e,0x2f] for s,p,c in [(0,0,3),(2,0,0),(2,0,3),(4,3,0),(4,4,0),(6,3,0),(6,4,0),(8,0,3)]]
 sw=[];tw=[];frames=set()
 for batch in range(4):
  f=3102+batch;data=b''.join(cases[batch*8:batch*8+8])+bytes(384)
  sw.append((f,0x600,data));tw.append((f,sy['world_actor_state'],data));frames.add(f)
 a,b=pair('matrix',frames,sw,tw);compare(a,b,frames,range(16),'matrix')
 # Source-selected random branches, each native choice explicitly controlled.
 decisions=[]
 for t,s,d,pose in [(0x2c,2,0,3),(0x2c,4,0,0),(0x2c,8,0,0),(0x2c,8,1,0),(0x2e,8,0,0),(0x2f,8,0,0)]:
  name=f'{t:02x}-{s}-{d}';data=bytes(record(t,s,d,pose))+bytes(720);a=ROOT/f'validation/sms-emerging-choice-{name}';b=ROOT/f'validation/md-emerging-choice-{name}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3102,a,{3102},[(200,220,0)]+PRESSES,ram_writes=[(3102,0x600,data),(3102,0x1600,bytes(1280))])
  expected=(a/'ram_03102.bin').read_bytes()[0x600:0x630]
  if t==0x2c and s in [2,4]:bits=expected[10];mask=3
  elif t==0x2c:bits=0 if expected[1]==4 else 4 if expected[1]==6 else 14;mask=15
  else:bits=(expected[4]+1)&31;mask=31
  seed=next(n for n in range(1,65536) if random_word(n)&mask==bits)
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',3102,b,{3102},PRESSES,ram_writes=[(3102,sy['world_actor_state'],data),(3102,sy['sms_vram']+0x3800,bytes(1280)),(3102,sy['randbase'],seed.to_bytes(2,'big'))])
  compare(a,b,{3102},[0],'choice');decisions.append(dict(type=t,state=s,direction=d,observed_next_state=expected[1],native_rng_controlled=True))
 # Find actual SMS accepted terrain appearances, then match only those RNG bits.
 spawns=[]
 for t,terrain in [(0x2e,8),(0x2f,8),(0x2e,0x57)]:
  data=bytes(record(t,0))+bytes(720);frames=set(range(3102,3166));cells=bytes([terrain])*160
  a=ROOT/f'validation/sms-emerging-spawn-{t:02x}-{terrain:02x}';b=ROOT/f'validation/md-emerging-spawn-{t:02x}-{terrain:02x}'
  sw=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1c00,cells),(f,0x2f,b'\x07')]]
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
  chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x601]==2)
  e=(a/f'ram_{chosen:05}.bin').read_bytes()[0x600:0x630];cell=((e[0x11]-16)&240)|(e[0x13]>>4)
  seed=next(n for n in range(1,65536) if random_word(n)&127==cell-16 and random_word(random_word(n))&3==e[10])
  tw=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['scratch']+0x800,cells),(f,sy['vtimer'],(7).to_bytes(4,'big')),(f,sy['randbase'],seed.to_bytes(2,'big'))]]
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=tw)
  compare(a,b,{chosen},[0],'spawn');spawns.append(dict(type=t,source_frame=chosen,cell=cell,terrain=terrain,native_rng_and_clock_controlled=True))
 rejected=[]
 for t,terrain in [(0x2e,0),(0x2f,0),(0x2f,0x57)]:
  data=bytes(record(t,0))+bytes(720);cells=bytes([terrain])*160
  a,b=pair(f'reject-{t:02x}-{terrain:02x}',{3102},[(3102,0x600,data),(3102,0x1c00,cells),(3102,0x2f,b'\x07')],[(3102,sy['world_actor_state'],data),(3102,sy['scratch']+0x800,cells),(3102,sy['vtimer'],(7).to_bytes(4,'big'))])
  compare(a,b,{3102},[0],'terrain refusal');assert (a/'ram_03102.bin').read_bytes()[0x601]==0;rejected.append(dict(type=t,terrain=terrain))
 # The new projectile14 shares the octant routine, with its own velocity table.
 sw=[];tw=[];aim_frames=set()
 for n,(dx,dy) in enumerate([(16,32),(32,16),(-16,32),(-32,16),(16,-32),(32,-16),(-16,-32),(-32,-16),(16,16),(-16,-16),(0,0)]):
  f=3102+n;hx=120+dx;hy=76+dy;data=bytearray(768);e=bytearray(48);e[0]=0x14;e[3]=0x28;e[0x11]=80;e[0x13]=120;data[384:432]=e
  sw.extend([(f,0x600,bytes(data)),(f,0x312,(hx<<8).to_bytes(2,'little')),(f,0x310,(hy<<8).to_bytes(2,'little'))]);tw.extend([(f,sy['world_actor_state'],bytes(data)),(f,sy['hero_x'],(hx<<8).to_bytes(2,'big')),(f,sy['hero_y'],(hy<<8).to_bytes(2,'big'))]);aim_frames.add(f)
 a,b=pair('aim14',aim_frames,sw,tw);compare(a,b,aim_frames,[8],'aim14')
 # Actual shot14/15 emissions and free projectile motion after parent removal.
 data=bytes(record(0x2e,4,pose=4))+bytes(record(0x2f,4,pose=4))+bytes(672);frames=set(range(3102,3210))
 sw=[(3102,0x600,data),(3103,0x600,bytes(384)),(3102,0x312,(32<<8).to_bytes(2,'little')),(3103,0x312,(240<<8).to_bytes(2,'little')),(3103,0x310,(144<<8).to_bytes(2,'little'))]
 tw=[(3102,sy['world_actor_state'],data),(3103,sy['world_actor_state'],bytes(384)),(3102,sy['hero_x'],(32<<8).to_bytes(2,'big')),(3103,sy['hero_x'],(240<<8).to_bytes(2,'big')),(3103,sy['hero_y'],(144<<8).to_bytes(2,'big'))]
 a,b=pair('shots',frames,sw,tw);compare(a,b,frames,range(8,10),'shots')
 first=(a/'ram_03102.bin').read_bytes();assert [first[0x600+48*s] for s in [8,9]]==[0x14,0x15]
 deaths=[dict(slot=s,frame=next(f for f in sorted(frames) if not (a/f'ram_{f:05}.bin').read_bytes()[0x600+s*48])) for s in [8,9]]
 # Four blocked and two unobstructed horizontal expiry transitions use no RNG.
 data=bytearray(768)
 for slot,d in enumerate([0,1,2,3]):data[slot*48:(slot+1)*48]=record(0x2c,8,d)
 a,b=pair('blocked',{3102},[(3102,0x600,bytes(data)),(3102,0x1600,bytes([0xa0])*1280)],[(3102,sy['world_actor_state'],bytes(data)),(3102,sy['sms_vram']+0x3800,bytes([0xa0])*1280)])
 compare(a,b,{3102},range(4),'blocked')
 for slot,d in enumerate([2,3]):data[slot*48:(slot+1)*48]=record(0x2c,8,d)
 a,b=pair('horizontal',{3102},[(3102,0x600,bytes(data)),(3102,0x1600,bytes(1280))],[(3102,sy['world_actor_state'],bytes(data)),(3102,sy['sms_vram']+0x3800,bytes(1280))]);compare(a,b,{3102},range(2),'horizontal')
 # Observe all three vertical decisions in the executing source, then control
 # a single equivalent native random choice for each. This is not the Z80R stream.
 frames=set(range(3102,3166));data=bytes(record(0x2c,8))+bytes(720);a=ROOT/'validation/sms-emerging-rest-search'
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1600,bytes(1280))]])
 rest_states=[]
 for state,bits in [(4,0),(6,4),(10,14)]:
  chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x601]==state);b=ROOT/f'validation/md-emerging-rest-{state}'
  seed=next(n for n in range(1,65536) if random_word(n)&15==bits)
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,bytes(1280)),(f,sy['randbase'],seed.to_bytes(2,'big'))]])
  compare(a,b,{chosen},[0],'rest decisions');rest_states.append(state)
 # Opening and closing animations run freely through emission and recovery.
 data=bytes(record(0x2e,2,timer=32))+bytes(record(0x2f,2,timer=32))+bytes(672);frames=set(range(3102,3252))
 a,b=pair('animation',frames,[(3102,0x600,data)],[(3102,sy['world_actor_state'],data)]);compare(a,b,frames,range(2),'free animations')
 observed_states=sorted({(a/f'ram_{f:05}.bin').read_bytes()[0x601] for f in frames});assert observed_states==[2,4,6,8]
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),deterministic_cases=32,random_branches=decisions,terrain_appearances=spawns,terrain_refusals=rejected,projectile14_aim_cases=11,projectile14_15_births_source_exact=True,projectile_motion_frames=108,projectile_culls=deaths,blocked_cases=4,horizontal_cases=2,vertical_decision_states=rest_states,free_animation_frames=150,free_animation_states=observed_states,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False)
 (ROOT/'validation/emerging_actors_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Emerging/resting actors + projectiles OK',flush=True)
if __name__=='__main__':main()
