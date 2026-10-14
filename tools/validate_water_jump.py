"""Executing-SMS comparison for water emergence/walking/leaping33/34."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(t,s,d=0,p=0,c=0,h=0x100):
  e=bytearray(48);e[0]=t;e[1]=s;e[2]=6;e[3]=0x28;e[4]=c;e[8:10]=bytes.fromhex('9d88');e[10]=d;e[11]=p;e[12]=3;e[13]=13;e[0x11]=80;e[0x13]=120;e[0x18]=30
  e[0x22:0x24]=(120*256+3).to_bytes(2,'little');e[0x26:0x28]=(80*256+7).to_bytes(2,'little');e[0x28:0x2a]=(0x420).to_bytes(2,'little');e[0x2a:0x2c]=h.to_bytes(2,'little');e[0x2c]=d;e[0x2e:0x30]=bytes.fromhex('c0ff');return e
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-water-jump-{name}';b=ROOT/f'validation/md-water-jump-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 cases=[record(0x33,s,d) for s in [0,2,4,6,8] for d in range(4)]
 cases +=[record(0x34,s,d,c=c) for s,c in [(0,3),(2,0),(2,3),(6,0),(8,3)] for d in range(4)]
 cases +=[record(t,s,d,p=p,h=h) for t in [0x33,0x34] for s,p,h in [(12,1,0x100),(12,2,0x100),(14,0,0),(16,0,0),(16,0,0x2000),(16,0,0x10),(18,2,0)] for d in range(4)]
 sw=[];tw=[];frames=set()
 for batch in range((len(cases)+7)//8):
  f=3102+batch;data=b''.join(cases[batch*8:batch*8+8]);data+=bytes(768-len(data));sw.append((f,0x600,data));tw.append((f,sy['world_actor_state'],data));frames.add(f)
 a,b=pair('matrix',frames,sw,tw);compare(a,b,frames,range(16),'water matrix')
 # Walking choices on water and all four side/vertical landing candidates.
 decisions=[]
 for t,state,x,p in [(0x34,4,120,0),(0x34,8,120,0),(0x34,8,128,0),(0x34,18,120,3),(0x33,18,120,3)]+[(0x34,10,x,0) for x in [56,120,216]]:
  e=record(t,state,p=p,h=0);e[0x13]=x;data=bytes(e)+bytes(720);name=f'{t:02x}-{state}-{x}';tiles=bytes([0xc0])*1536
  a=ROOT/f'validation/sms-water-jump-choice-{name}';b=ROOT/f'validation/md-water-jump-choice-{name}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3102,a,{3102},[(200,220,0)]+PRESSES,ram_writes=[(3102,0x600,data),(3102,0x1600,tiles)])
  expected=(a/'ram_03102.bin').read_bytes()[0x600:0x630]
  if state==4 or (state==18 and t==0x34):bits=expected[10];mask=3
  elif state==18:bits=(expected[4]+1)&15;mask=15
  elif state==8:bits=0 if expected[1]==4 else 8 if expected[1]==10 or x==128 and expected[1]==4 else 2;mask=15
  else:bits=expected[0x2c];mask=3
  seed=next(n for n in range(1,65536) if random_word(n)&mask==bits)
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',3102,b,{3102},PRESSES,ram_writes=[(3102,sy['world_actor_state'],data),(3102,sy['sms_vram']+0x3800,tiles),(3102,sy['randbase'],seed.to_bytes(2,'big'))])
  compare(a,b,{3102},range(16),'water choices');decisions.append(dict(type=t,state=state,x=x,next_state=expected[1],native_rng_choice_controlled=True))
 # Appearance tests: accepted water cells, required water at the destination,
 # and a rejected ground cell. Eligibility and native RNG bits are controlled.
 appearances=[]
 for t,water_destination in [(0x33,True),(0x33,False),(0x34,True)]:
  name=f'{t:02x}-{int(water_destination)}';e=record(t,10 if t==0x33 else 0,h=0);data=bytes(e)+bytes(720);frames=set(range(3102,3166));tiles=bytes([0xc0 if water_destination else 0])*1536;cells=bytes([8])*160;a=ROOT/f'validation/sms-water-jump-appearance-{name}';b=ROOT/f'validation/md-water-jump-appearance-{name}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1600,tiles),(f,0x1c00,cells),(f,0x2f,b'\x07')]])
  expected_state=12 if t==0x33 and water_destination else 2
  chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x601]==expected_state);expected=(a/f'ram_{chosen:05}.bin').read_bytes()[0x600:0x630];cell=((expected[0x11]-16)&240)|(expected[0x13]>>4)
  def acceptable(n):
   r=random_word(n)
   if r&127!=cell-16:return False
   r=random_word(r)
   if t==0x34:return r&3==expected[10]
   choice=random_word(r)&3
   if choice<2 and expected[0x13]<72:choice|=2
   elif choice>=2 and expected[0x13]>=200:choice&=1
   return choice==expected[0x2c]
  seed=next(n for n in range(1,65536) if acceptable(n))
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,tiles),(f,sy['scratch']+0x800,cells),(f,sy['vtimer'],(7).to_bytes(4,'big')),(f,sy['randbase'],seed.to_bytes(2,'big'))]])
  compare(a,b,{chosen},[0],'water appearance');appearances.append(dict(type=t,source_frame=chosen,next_state=expected_state,water_destination=water_destination,native_rng_and_phase_controlled=True))
 terrain_refusals=[]
 for t in [0x33,0x34]:
  data=bytes(record(t,10 if t==0x33 else 0,h=0))+bytes(720);tiles=bytes([0xc0])*1536
  a,b=pair(f'ground-refusal-{t:02x}',{3102},[(3102,0x600,data),(3102,0x1600,tiles),(3102,0x1c00,bytes(160)),(3102,0x2f,b'\x07')],[(3102,sy['world_actor_state'],data),(3102,sy['sms_vram']+0x3800,tiles),(3102,sy['scratch']+0x800,bytes(160)),(3102,sy['vtimer'],(7).to_bytes(4,'big'))])
  compare(a,b,{3102},[0],'ground refusal');assert (a/'ram_03102.bin').read_bytes()[0x601]==(10 if t==0x33 else 0);terrain_refusals.append(t)
 # Force an actual source walking decision8 on an aligned water cell, then
 # compare the transition that stops movement and prepares its leap attempt.
 e=record(0x34,8,h=0);data=bytes(e)+bytes(720);frames=set(range(3102,3230));tiles=bytes([0xc0])*1536;a=ROOT/'validation/sms-water-jump-walking-search';b=ROOT/'validation/md-water-jump-walking-special'
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3229,a,frames,[(200,220,0)]+PRESSES,ram_writes=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1600,tiles)]])
 chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x601]==10);seed=next(n for n in range(1,65536) if random_word(n)&15==8)
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,tiles),(f,sy['randbase'],seed.to_bytes(2,'big'))]])
 compare(a,b,{chosen},[0],'walking special');walking_special_frame=chosen
 # Leap from each of the four vectors, with no further actor injections.
 data=bytearray(768)
 for slot,d in enumerate(range(4)):
  e=record(0x34,14,d,h=0);data[slot*48:(slot+1)*48]=e
 frames=set(range(3102,3140));a,b=pair('free-leap',frames,[(3102,0x600,bytes(data)),(3102,0x312,(32<<8).to_bytes(2,'little'))],[(3102,sy['world_actor_state'],bytes(data)),(3102,sy['hero_x'],(32<<8).to_bytes(2,'big'))]);compare(a,b,frames,range(16),'free ballistic leap and shots')
 birth_frames=[]
 for f in sorted(frames):
  raw=(a/f'ram_{f:05}.bin').read_bytes()
  if any(raw[0x600+48*s]==0x13 for s in range(8,16)):birth_frames.append(f)
 assert birth_frames,('aimed shot at height32 absent')
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),deterministic_cases=len(cases),controlled_decisions=decisions,appearance_cases=appearances,ground_refusal_types=terrain_refusals,walking_special_source_frame=walking_special_frame,free_leap_frames=38,free_leap_vectors=4,aimed13_active_frames=birth_frames,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False,natural_gameplay_verified=False)
 (ROOT/'validation/water_jump_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Water jumps/walks + ballistic vectors + aimed shots OK',flush=True)
if __name__=='__main__':main()
