"""Compare flying integer arithmetic and aimed shots with the original SMS core."""
import contextlib, hashlib, io, json, re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(t,state,variant):
  e=bytearray(48);e[0]=t;e[1]=state;e[2]=6;e[3]=0x28;e[4]=20;e[11]=3 if state==2 else 0;e[12]=2;e[13]=5
  e[8:10]=bytes.fromhex('fa84' if state==2 else 'ee85');e[0x11]=80;e[0x13]=120;e[0x18]=32
  e[0x25:0x29]=(120*256+variant).to_bytes(2,'little')+(80*256+variant).to_bytes(2,'little')
  e[0x29]=(variant*31)&255;e[0x2a]=[0,16,255,17][variant%4];e[0x2b]=[0,12,255,13][variant%4]
  vx=[0,0x1ff,0x200,0xffff,0xfe00,0xfdff,0x8000,0x7fff][variant%8]
  e[0x21:0x25]=vx.to_bytes(2,'little')+((vx+3)&65535).to_bytes(2,'little')
  if variant>=8:e[0x26]=[31,32,223,224][variant%4];e[0x28]=[31,32,119,120][variant%4]
  return e
 cases=[(t,s,v) for t in range(0x23,0x26) for s,variants in [(2,range(8)),(4,range(12))] for v in variants]
 sw=[];tw=[];frames=set()
 for batch in range((len(cases)+7)//8):
  f=3102+batch;data=bytearray(768)
  for slot,(t,s,v) in enumerate(cases[batch*8:batch*8+8]):data[slot*48:(slot+1)*48]=record(t,s,v)
  sw.append((f,0x600,bytes(data)));tw.append((f,sy['world_actor_state'],bytes(data)));frames.add(f)
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-flying-{name}';b=ROOT/f'validation/md-flying-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 a,b=pair('matrix',frames,sw,tw);compare(a,b,frames,range(16),'flying arithmetic')
 # Eight aim octants plus ties, with the target position injected identically.
 targets=[(120+dx,76+dy) for dx,dy in [(16,32),(32,16),(-16,32),(-32,16),(16,-32),(32,-16),(-16,-32),(-32,-16),(16,16),(-16,-16),(0,0)]]
 sw=[];tw=[];frames=set()
 for i,(hx,hy) in enumerate(targets):
  f=3102+i;data=bytearray(768)
  for slot,t in enumerate([0x13,0x15]):
   e=bytearray(48);e[0]=t;e[3]=0x28;e[0x11]=80;e[0x13]=120;data[(slot+8)*48:(slot+9)*48]=e
  sw.extend([(f,0x600,bytes(data)),(f,0x312,(hx<<8).to_bytes(2,'little')),(f,0x310,(hy<<8).to_bytes(2,'little'))])
  tw.extend([(f,sy['world_actor_state'],bytes(data)),(f,sy['hero_x'],(hx<<8).to_bytes(2,'big')),(f,sy['hero_y'],(hy<<8).to_bytes(2,'big'))]);frames.add(f)
 a,b=pair('aim',frames,sw,tw);compare(a,b,frames,range(8,10),'aimed shot')
 # Three flyers run freely for 160 ticks, with a fixed target and shots delayed.
 data=bytearray(768)
 for slot,t in enumerate(range(0x23,0x26)):
  e=record(t,4,0);e[4]=255;data[slot*48:(slot+1)*48]=e
 frames=set(range(3102,3262));sw=[(3102,0x600,bytes(data))];tw=[(3102,sy['world_actor_state'],bytes(data))]
 a,b=pair('motion',frames,sw,tw);compare(a,b,frames,range(3),'free flying motion')
 data=bytearray(768)
 for slot,t in enumerate([0x24,0x25]):
  e=record(t,4,0);e[4]=0;data[slot*48:(slot+1)*48]=e
 frames=set(range(3102,3210))
 sw=[(3102,0x600,bytes(data)),(3103,0x600,bytes(384)),(3102,0x312,(32<<8).to_bytes(2,'little')),(3103,0x312,(240<<8).to_bytes(2,'little')),(3103,0x310,(144<<8).to_bytes(2,'little'))]
 tw=[(3102,sy['world_actor_state'],bytes(data)),(3103,sy['world_actor_state'],bytes(384)),(3102,sy['hero_x'],(32<<8).to_bytes(2,'big')),(3103,sy['hero_x'],(240<<8).to_bytes(2,'big')),(3103,sy['hero_y'],(144<<8).to_bytes(2,'big'))]
 a,b=pair('birth-lifetime',frames,sw,tw);compare(a,b,frames,range(8,10),'aimed birth/lifetime')
 first=(a/'ram_03102.bin').read_bytes();assert [first[0x600+slot*48] for slot in [8,9]]==[0x13,0x15]
 assert first[0x604]==first[0x634]==127,('firing countdown')
 deaths=[]
 for slot in [8,9]:
  f=next(f for f in sorted(frames) if not (a/f'ram_{f:05}.bin').read_bytes()[0x600+slot*48]);deaths.append(dict(slot=slot,frame=f))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),arithmetic_cases=len(cases),aimed_projectile_types=[0x13,0x15],aim_targets=len(targets),free_motion_frames=160,projectile_births_source_exact=True,projectile_lifetime_frames=108,projectile_culls=deaths,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False)
 (ROOT/'validation/flying_actors_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Flying arithmetic60 + aimed22 + free motion160 OK',flush=True)
if __name__=='__main__':main()
