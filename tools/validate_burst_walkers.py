"""Compare source36/37 walking, transient pool and19/1E flight."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(t,s,d=0,c=0,pose=2):
  e=bytearray(48);e[0]=t;e[1]=s;e[2]=6;e[3]=0x28;e[4]=c;e[8:10]=bytes.fromhex('b789');e[10]=d;e[11]=pose;e[12]=2;e[13]=10;e[0x11]=80;e[0x13]=120;e[0x18]=30;return e
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q])
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-burst-{name}';b=ROOT/f'validation/md-burst-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 cases=[record(t,s,d,c) for t in [0x36,0x37] for s,c in [(2,0),(4,0),(8,0),(10,3)] for d in range(4)]
 sw=[];tw=[];frames=set()
 for batch in range(4):
  f=3102+batch;data=b''.join(cases[batch*8:batch*8+8])+bytes(384);sw.append((f,0x600,data));tw.append((f,sy['world_actor_state'],data));frames.add(f)
 a,b=pair('matrix',frames,sw,tw);compare(a,b,frames,range(16),'matrix')
 print('32 deterministic walker records OK',flush=True)
 decisions=[];tiles=bytes(1536)
 for t in [0x36,0x37]:
  for state in [2,4,6,10]:
   data=bytes(record(t,state,pose=3))+bytes(720);f=3102
   a=ROOT/f'validation/sms-burst-decision-{t}-{state}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',f,a,{f},[(200,220,0)]+PRESSES,ram_writes=[(f,0x600,data),(f,0x1600,tiles),(f,0x1b,b'\0')])
   src=(a/f'ram_{f:05}.bin').read_bytes();e=src[0x600:0x630];shoot=bool(src[0x780]);mask=15 if t==0x36 else 7
   def valid(seed):
    q=random_word(seed)
    if state!=10:return q&3==e[10]
    if (q&mask==0)!=shoot:return False
    r=random_word(q)&15
    return (6 if r<2 or r>=8 else 8)==e[1]
   seed=next(n for n in range(1,65536) if valid(n));b=ROOT/f'validation/md-burst-decision-{t}-{state}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',f,b,{f},PRESSES,ram_writes=[(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,tiles),(f,sy['randbase'],seed.to_bytes(2,'big'))])
   compare(a,b,{f},[0],'controlled decision')
   # Straight19 uses a separately tested clock phase; compare emission slots/directions here.
   md=native(b,f)[sy['world_actor_state']:sy['world_actor_state']+768]
   assert [src[0x600+n*48] for n in range(8,16)]==[md[n*48] for n in range(8,16)]
   assert [src[0x60a+n*48] for n in range(8,16)]==[md[10+n*48] for n in range(8,16)]
   decisions.append(dict(type=t,state=state,next_state=e[1],shoot=shoot,native_random_controlled=True))
 print('8 source-observed decisions OK',flush=True)
 # Direct aimed1E: all octants, ties and zero vector, then108 frames of free flight.
 aims=[]
 for hx,hy in [(120,16),(120,144),(48,80),(208,80),(48,16),(208,16),(48,144),(208,144),(120,76),(116,72),(124,80)]:
  data=bytes(384)+bytes(record(0x1e,0,pose=0))+bytes(336);f=3102;frames=set(range(f,f+108))
  sw=[(f,0x600,data),(f,0x312,(hx<<8).to_bytes(2,'little')),(f,0x310,(hy<<8).to_bytes(2,'little'))]
  tw=[(f,sy['world_actor_state'],data),(f,sy['hero_x'],(hx<<8).to_bytes(2,'big')),(f,sy['hero_y'],(hy<<8).to_bytes(2,'big'))]
  a,b=pair(f'aim-{hx}-{hy}',frames,sw,tw);compare(a,b,frames,[8],'aim1E')
  aims.append(dict(x=hx,y=hy,free_frames=108))
 print('11 aimed1E trajectories OK',flush=True)
 # Clock phase is aligned explicitly: the global original clock/R stream is not claimed.
 phases=[]
 for phase in [0,1]:
  data=bytes(384)+b''.join(bytes(record(0x19,0,d,pose=0)) for d in range(4))+bytes(192);f=3102;frames=set(range(f,f+108))
  sw=[(f,0x600,data),(f,0x2f,bytes([phase])),(f,0x312,(240<<8).to_bytes(2,'little')),(f,0x310,(144<<8).to_bytes(2,'little'))]
  a=ROOT/f'validation/sms-burst-phase-{phase}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
  for shift in [0,1]:
   b=ROOT/f'validation/md-burst-phase-{phase}-{shift}'
   tw=[(f,sy['world_actor_state'],data),(f,sy['world_clock_shift'],shift.to_bytes(4,'big')),(f,sy['hero_x'],(240<<8).to_bytes(2,'big')),(f,sy['hero_y'],(144<<8).to_bytes(2,'big'))]
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x780:0x840];dst=native(b,f)[sy['world_actor_state']+384:sy['world_actor_state']+576]
   if src[20:24]==dst[20:24]:break
  compare(a,b,frames,range(8,12),'projectile19 phase')
  phases.append(dict(source_clock_injected=phase,native_shift=shift,directions=4,free_frames=108))
 print('19 cardinal/diagonal phases OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),deterministic_cases=32,controlled_decisions=decisions,aimed1e=aims,projectile19_phases=phases,collision_descriptor_bytes_excluded=[27,28],sprite_overflow_suppression_verified=False,original_rng_or_clock_stream_verified=False,natural_gameplay_verified=False)
 (ROOT/'validation/burst_walkers_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

