"""Compare31/32 jumping bodies and adjacent30 shadows to the executing SMS."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(t,state,v=0):
  e=bytearray(48);e[0]=t;e[1]=state;e[2]=6;e[3]=0x28;e[8:10]=bytes.fromhex('fa84' if state==2 else '7188');e[11]=3 if state==2 else 0;e[12]=4 if state==2 else 0;e[13]=16;e[0x11]=80;e[0x13]=120;e[0x18]=30
  e[0x22:0x24]=(120*256+v).to_bytes(2,'little');e[0x26:0x28]=(80*256+v).to_bytes(2,'little')
  e[0x20:0x22]=[0,0x80,0xff80,0xffff][v%4].to_bytes(2,'little');e[0x24:0x26]=[0,0x100,0xff00,0xffff][v%4].to_bytes(2,'little')
  e[0x28:0x2a]=[0,0x210,0xffe0,0x8000][v%4].to_bytes(2,'little');e[0x2a:0x2c]=[0x100,0x2f0,0x400,0x7fff][v%4].to_bytes(2,'little')
  return e
 def child():
  e=bytearray(48);e[0]=0x30;e[2]=6;return e
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-jumping-{name}';b=ROOT/f'validation/md-jumping-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 cases=[(t,s,v) for t in [0x31,0x32] for s in [2,4,6,10] for v in range(4)];frames=set();sw=[];tw=[]
 for batch in range(8):
  f=3102+batch;data=bytearray(768)
  for slot,(t,s,v) in enumerate(cases[batch*4:batch*4+4]):data[slot*96:slot*96+48]=record(t,s,v);data[slot*96+48:slot*96+96]=bytes(48) if s==2 else child()
  sw.append((f,0x600,bytes(data)));tw.append((f,sy['world_actor_state'],bytes(data)));frames.add(f)
 a,b=pair('arithmetic',frames,sw,tw);compare(a,b,frames,range(16),'arithmetic/shadows')
 for f in [3102,3106]:
  raw=(a/f'ram_{f:05}.bin').read_bytes()
  assert all(raw[0x600+slot*96+48]==0x30 and raw[0x600+slot*96+50]==6 for slot in range(4))
 data=bytearray(768)
 for slot,t in enumerate([0x31,0x32]):
  e=record(t,2);e[11]=2;data[slot*96:slot*96+48]=e
 a,b=pair('appearance-wait',{3102},[(3102,0x600,bytes(data))],[(3102,sy['world_actor_state'],bytes(data))]);compare(a,b,{3102},range(4),'appearance wait')
 assert (a/'ram_03102.bin').read_bytes()[0x630:0x660]==bytes(48)
 # Source executes each random-dependent decision. Choose the native single
 # random result to produce that observed vector, boundary rejection or state.
 decisions=[]
 for t,state,border,blocked in [(t,s,b,c) for t in [0x31,0x32] for s,b,c in [(6,0,False),(8,0,False),(10,0,False),(8,1,False),(8,2,False),(8,0,True)]]:
  e=record(t,state);e[0x2a:0x2c]=bytes(2)
  if border:e[0x23]=e[0x13]=24 if border==1 else 232;e[0x27]=e[0x11]=32 if border==1 else 144
  data=bytes(e)+bytes(child())+bytes(672);tiles=bytes([0xe0 if blocked else 0])*1536;name=f'{t:02x}-{state}-{int(border)}-{int(blocked)}'
  a=ROOT/f'validation/sms-jumping-choice-{name}';b=ROOT/f'validation/md-jumping-choice-{name}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3102,a,{3102},[(200,220,0)]+PRESSES,ram_writes=[(3102,0x600,data),(3102,0x1600,tiles)])
  expected=(a/'ram_03102.bin').read_bytes()[0x600:0x630]
  if state==6:bits=0 if expected[1]==8 else 1;mask=3
  elif expected[1]==10:
   vectors=(ROOT/'input/original.sms').read_bytes()[0x8ca3+(64 if t==0x32 else 0):0x8ce3+(64 if t==0x32 else 0)]
   bits=next(i for i in range(8) if vectors[i*8:i*8+2]==expected[0x20:0x22] and vectors[i*8+2:i*8+4]==expected[0x24:0x26] and vectors[i*8+7]==expected[10]);mask=7
  else:
   # A rejected vector's direction is not stored. Select any actual rejecting
   # source vector for the controlled boundary, or any vector for a solid map.
   vectors=(ROOT/'input/original.sms').read_bytes()[0x8ca3+(64 if t==0x32 else 0):0x8ce3+(64 if t==0x32 else 0)]
   bits=next(i for i in range(8) if blocked or vectors[i*8+4]&(5 if border==1 else 10));mask=7
  seed=next(n for n in range(1,65536) if random_word(n)&mask==bits)
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',3102,b,{3102},PRESSES,ram_writes=[(3102,sy['world_actor_state'],data),(3102,sy['sms_vram']+0x3800,tiles),(3102,sy['randbase'],seed.to_bytes(2,'big'))])
  compare(a,b,{3102},range(2),'controlled decision');decisions.append(dict(type=t,state=state,border=border,solid_tilemap=blocked,observed_next_state=expected[1],native_rng_choice_controlled=True))
 # Observe all eight source vectors for both types, then match each isolated
 # decision. No recorded actor state is incorporated in the game assets.
 vector_cases=[]
 for t in [0x31,0x32]:
  e=record(t,8);e[0x2a:0x2c]=bytes(2);data=bytes(e)+bytes(child())+bytes(672);frames=set(range(3102,3230));tiles=bytes(1536);a=ROOT/f'validation/sms-jumping-vectors-{t:02x}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3229,a,frames,[(200,220,0)]+PRESSES,ram_writes=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1600,tiles)]])
  vectors=(ROOT/'input/original.sms').read_bytes()[0x8ca3+(64 if t==0x32 else 0):0x8ce3+(64 if t==0x32 else 0)]
  for choice in range(8):
   chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x620:0x622]==vectors[choice*8:choice*8+2] and (a/f'ram_{f:05}.bin').read_bytes()[0x624:0x626]==vectors[choice*8+2:choice*8+4])
   seed=next(n for n in range(1,65536) if random_word(n)&7==choice);b=ROOT/f'validation/md-jumping-vector-{t:02x}-{choice}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,tiles),(f,sy['randbase'],seed.to_bytes(2,'big'))]])
   compare(a,b,{chosen},range(2),'all vectors');vector_cases.append(dict(type=t,vector=choice,source_frame=chosen,native_rng_choice_controlled=True))
 # Free arithmetic/shadow evolution without further body or shadow injections.
 data=bytearray(768)
 for slot,t in enumerate([0x31,0x32]):
  e=record(t,10);e[0x28:0x2a]=(1024).to_bytes(2,'little');e[0x2a:0x2c]=(4096).to_bytes(2,'little');data[slot*96:slot*96+48]=e;data[slot*96+48:slot*96+96]=child()
 frames=set(range(3102,3120));a,b=pair('free',frames,[(3102,0x600,bytes(data))],[(3102,sy['world_actor_state'],bytes(data))]);compare(a,b,frames,range(4),'free arithmetic')
 # Explosion initialization clears an adjacent shadow before its slot is ticked.
 e=bytearray(48);e[0]=1;e[7]=0x31;e[0x11]=80;e[0x13]=120;data=bytes(e)+bytes(child())+bytes(672)
 a,b=pair('death',{3102},[(3102,0x600,data)],[(3102,sy['world_actor_state'],data)]);compare(a,b,{3102},range(2),'shadow death cleanup');assert (a/'ram_03102.bin').read_bytes()[0x630:0x660]==bytes(48)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),arithmetic_body_cases=32,shadow_birth_into_empty_record_verified=True,appearance_wait_without_shadow_verified=True,controlled_random_cases=decisions,all_sixteen_vector_cases=vector_cases,free_body_shadow_frames=18,adjacent_shadow_removal_source_exact=True,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False,natural_gameplay_verified=False)
 (ROOT/'validation/jumping_actors_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Jumping bodies/shadows/arithmetic/decisions/death OK',flush=True)
if __name__=='__main__':main()
