"""Execute SMS5878 and89D8 branches, compare native placements and emissions."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rom=(ROOT/'input/original.sms').read_bytes()
 def record(state=0,timer=0):
  e=bytearray(48);e[0]=0x2d;e[1]=state;e[3]=0x28;e[4]=timer;e[0x11]=80;e[0x13]=120;return e
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-fixed-{name}';b=ROOT/f'validation/md-fixed-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 rows=[];sw=[];tw=[];frames=set()
 for cls,start,count,base,end in [(0,0x58bc,11,0x58c7,0x5919),(1,0x5919,57,0x5952,0x5b20)]:
  pointers=[int.from_bytes(rom[base+n*2:base+n*2+2],'little') for n in range(count)]
  for room in rom[start:start+count]:
   # CPIR uses the first occurrence, including the duplicate5D in class1.
   i=rom[start:start+count].index(room);p=pointers[count-i-1]
   limit=min([a for a in pointers if a>p]+[end]);slots=(limit-p)//2;assert 1<=slots<=8,(cls,room,slots)
   f=3102+len(rows);data=b''.join(record() for _ in range(slots))+bytes(768-slots*48)
   sw.extend([(f,0x600,data),(f,0xb9,bytes([room,cls]))]);tw.extend([(f,sy['world_actor_state'],data),(f,sy['room_id'],(room|(cls<<8)).to_bytes(2,'big'))]);frames.add(f)
   rows.append(dict(frame=f,room=room,region=cls,slots=slots,pointer=p))
 a,b=pair('placement',frames,sw,tw);compare(a,b,frames,range(16),'placement')
 for row in rows:
  raw=(a/f"ram_{row['frame']:05}.bin").read_bytes()
  for slot in range(row['slots']):
   e=raw[0x600+slot*48:0x630+slot*48];assert e[1]==2 and e[4]==63 and not e[3]&1
   assert bytes([e[0x13],e[0x11]])==rom[row['pointer']+slot*2:row['pointer']+slot*2+2]
 # C0BA is the region byte of the room ID, independent of background graphics.
 # Force the native graphics selector differently while preserving region0.
 data=bytes(record())+bytes(720)
 a,b=pair('region-not-graphics',{3102},[(3102,0x600,data),(3102,0xb9,b'\x51\x00')],[(3102,sy['world_actor_state'],data),(3102,sy['room_id'],(0x51).to_bytes(2,'big')),(3102,sy['world_graphics_class'],(1).to_bytes(2,'big'))])
 compare(a,b,{3102},[0],'region independent of graphics')
 default_cases=[]
 for room in [0xa4,0x1aa]:
  data=bytes(record())+bytes(record())+bytes(672)
  a,b=pair(f'unknown-room-{room:03x}',{3102},[(3102,0x600,data),(3102,0xb9,room.to_bytes(2,'little'))],[(3102,sy['world_actor_state'],data),(3102,sy['room_id'],room.to_bytes(2,'big'))])
  compare(a,b,{3102},range(2),'CPIR default pointer');default_cases.append(room)
 # Waiting is deterministic and preserves the hidden fixed position.
 data=bytes(record(2,64))+bytes(720);frames=set(range(3102,3166))
 a,b=pair('waiting',frames,[(3102,0x600,data)],[(3102,sy['world_actor_state'],data)]);compare(a,b,frames,range(16),'waiting')
 assert (a/'ram_03165.bin').read_bytes()[0x604]==0
 # Search source decisions; native RNG bits are selected to reproduce each
 # observed branch and delay, not to replace the complete Z80 refresh stream.
 frames=set(range(3102,3166));data=bytes(record(2))+bytes(720);a=ROOT/'validation/sms-fixed-choices'
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=[(f,0x600,data) for f in sorted(frames)])
 branches=[];birth_frame=None
 for shoot in [False,True]:
  chosen=next(f for f in sorted(frames) if bool((a/f'ram_{f:05}.bin').read_bytes()[0x780])==shoot)
  expected=(a/f'ram_{chosen:05}.bin').read_bytes();bits=expected[0x604]+1-113;assert 0<=bits<16
  seed=next(n for n in range(1,65536) if ((random_word(n)&15)>=8)==shoot and random_word(random_word(n))&15==bits)
  b=ROOT/f'validation/md-fixed-choice-{int(shoot)}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['randbase'],seed.to_bytes(2,'big'))]])
  compare(a,b,{chosen},range(16),'shoot/delay');branches.append(dict(shoot=shoot,source_frame=chosen,post_tick_delay=expected[0x604],native_rng_controlled=True))
  if shoot:birth_frame=chosen;birth_seed=seed
 # Follow one actually emitted14 without projectile reinjection; move target
 # away after initialization and remove parent to isolate projectile lifetime.
 frames=set(range(birth_frame,birth_frame+108));sw=[(birth_frame,0x600,data),(birth_frame+1,0x600,bytes(384)),(birth_frame+1,0x312,(240<<8).to_bytes(2,'little')),(birth_frame+1,0x310,(144<<8).to_bytes(2,'little'))]
 # Replay the same source instruction history up to the chosen decision.
 sw=[(f,0x600,data) for f in range(3102,birth_frame)]+sw
 tw=[w for f in range(3102,birth_frame+1) for w in [(f,sy['world_actor_state'],data),(f,sy['randbase'],birth_seed.to_bytes(2,'big'))]]+[(birth_frame+1,sy['world_actor_state'],bytes(384)),(birth_frame+1,sy['hero_x'],(240<<8).to_bytes(2,'big')),(birth_frame+1,sy['hero_y'],(144<<8).to_bytes(2,'big'))]
 a,b=pair('lifetime',frames,sw,tw);compare(a,b,frames,[8],'projectile lifetime')
 assert (a/f'ram_{birth_frame:05}.bin').read_bytes()[0x780]==0x14
 death=next(f for f in sorted(frames) if not (a/f'ram_{f:05}.bin').read_bytes()[0x780])
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),placement_rows=rows,placement_cases=sum(r['slots'] for r in rows),default_pointer_rooms=default_cases,first_duplicate_room_match_verified=True,region_independent_of_graphics_verified=True,waiting_frames=64,controlled_random_branches=branches,projectile14_birth_source_exact=True,projectile14_motion_frames=108,projectile14_cull_frame=death,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False,natural_gameplay_route_verified=False)
 (ROOT/'validation/fixed_shooter_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Fixed placements + hidden shooter + projectile14 OK',flush=True)
if __name__=='__main__':main()
