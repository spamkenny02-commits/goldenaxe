"""Source-core comparisons for hidden35 trap activation, terrain and projectile16."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def record(s,d=0,c=0):
  e=bytearray(48);e[0]=0x35;e[1]=s;e[2]=6;e[3]=0x28;e[4]=c;e[8:10]=bytes.fromhex('8d89');e[10]=d;e[12]=2;e[13]=10;e[0x11]=80;e[0x13]=120;e[0x18]=30;return e
 def compare(a,b,frames,slots,label):
  for f in sorted(frames):
   src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   for slot in slots:
    x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
    assert x[:27]+x[29:]==y[:27]+y[29:],(label,f,slot,[(n,p,q) for n,(p,q) in enumerate(zip(x,y)) if p!=q],x.hex(),y.hex())
 def pair(name,frames,sw,tw):
  a=ROOT/f'validation/sms-trap-{name}';b=ROOT/f'validation/md-trap-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',max(frames),a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',max(frames),b,frames,PRESSES,ram_writes=tw)
  return a,b
 cases=[record(s,d,c) for s,c in [(2,0),(4,3),(8,0),(10,3)] for d in range(4)];sw=[];tw=[];frames=set()
 for batch in range(2):
  f=3102+batch;data=b''.join(cases[batch*8:batch*8+8])+bytes(384);sw.append((f,0x600,data));tw.append((f,sy['world_actor_state'],data));frames.add(f)
 a,b=pair('matrix',frames,sw,tw);compare(a,b,frames,range(16),'trap matrix')
 # Placement uses BC11 even in region1, and CPIR exhaustion selects entry0.
 placements=[]
 for room in [0x51,0xc4,0xf5,0xa4,0x118,0x1aa]:
  data=bytes(record(0))+bytes(720);a,b=pair(f'place-{room:03x}',{3102},[(3102,0x600,data),(3102,0xb9,room.to_bytes(2,'little'))],[(3102,sy['world_actor_state'],data),(3102,sy['room_id'],room.to_bytes(2,'big'))]);compare(a,b,{3102},[0],'trap placement');placements.append(room)
 terrain=[]
 # Proximity thresholds: activation strictly inside24/32. Every active case
 # compares the logical cell and all tilemap bytes after source49A9.
 for hx,hy,tile,lower in [(143,111,0,False),(144,80,0,False),(120,112,0,False),(97,49,0x6b,False),(96,80,0,False),(120,48,0,False),(120,80,0x6b,True),(120,80,0,True)]:
  data=bytes(record(2))+bytes(720);name=f'{hx}-{hy}-{tile}-{int(lower)}';sw=[(3102,0x600,data),(3102,0x312,(hx<<8).to_bytes(2,'little')),(3102,0x310,(hy<<8).to_bytes(2,'little')),(3102,0x1600+7*64+28,bytes([tile]))];tw=[(3102,sy['world_actor_state'],data),(3102,sy['hero_x'],(hx<<8).to_bytes(2,'big')),(3102,sy['hero_y'],(hy<<8).to_bytes(2,'big')),(3102,sy['sms_vram']+0x3800+7*64+28,bytes([tile]))]
  if lower:sw.append((3102,0x1600+10*64+28,b'\x53'));tw.append((3102,sy['sms_vram']+0x3800+10*64+28,b'\x53'))
  a,b=pair(f'terrain-{name}',{3102},sw,tw);compare(a,b,{3102},[0],'proximity');src=(a/'ram_03102.bin').read_bytes();md=native(b,3102)
  assert src[0x1c00:0x1ca0]==md[sy['scratch']+0x800:sy['scratch']+0x8a0],(name,'logical cells')
  assert src[0x1600:0x1b00]==md[sy['sms_vram']+0x3800:sy['sms_vram']+0x3d00],(name,'tilemap')
  active=abs(hx-120)<24 and abs(hy-80)<32;assert src[0x601]==(4 if active else 2)
  terrain.append(dict(hero_x=hx,hero_y=hy,activated=active,first_tile=tile,lower_tile53=lower,logical_and_tilemap_source_exact=True))
 # Source decisions on a clear map; reproduce its single/double random bits.
 decisions=[]
 for state in [4,6,10]:
  data=bytes(record(state))+bytes(720);tiles=bytes(1536);frames=set(range(3102,3166));a=ROOT/f'validation/sms-trap-decisions-{state}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=[w for f in sorted(frames) for w in [(f,0x600,data),(f,0x1600,tiles)]])
  chosen=3102;expected=(a/f'ram_{chosen:05}.bin').read_bytes();e=expected[0x600:0x630];shoot=bool(expected[0x780])
  def valid(n):
   r=random_word(n)
   if state in [4,6]:return r&3==e[10]
   if (r&15==0)!=shoot:return False
   q=random_word(r)&15
   if q<2:return e[1]==6 and e[10]==0
   if q<8:return e[1]==8 and e[10]==0
   return e[1]==6 and e[10]==0 # source aligns upward to hero120/16
  seed=next(n for n in range(1,65536) if valid(n));b=ROOT/f'validation/md-trap-decision-{state}'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=[(chosen,sy['world_actor_state'],data),(chosen,sy['sms_vram']+0x3800,tiles),(chosen,sy['randbase'],seed.to_bytes(2,'big'))])
  compare(a,b,{chosen},range(16),'decisions');decisions.append(dict(state=state,next_state=e[1],shot=shoot,native_rng_controlled=True))
 # Find a real shot16 and follow it freely after removing the parent.
 frames=set(range(3102,3166));a=ROOT/'validation/sms-trap-decisions-10';chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x780]==0x16);expected=(a/f'ram_{chosen:05}.bin').read_bytes();e=expected[0x600:0x630]
 seed=next(n for n in range(1,65536) if random_word(n)&15==0 and ((random_word(random_word(n))&15)<2 or (random_word(random_word(n))&15)>=8)==(e[1]==6))
 data=bytes(record(10))+bytes(720);tiles=bytes(1536);frames=set(range(chosen,chosen+108))
 sw=[w for f in range(3102,chosen+1) for w in [(f,0x600,data),(f,0x1600,tiles)]]+[(chosen+1,0x600,bytes(384)),(chosen+1,0x312,(240<<8).to_bytes(2,'little')),(chosen+1,0x310,(144<<8).to_bytes(2,'little'))]
 tw=[w for f in range(3102,chosen+1) for w in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,tiles),(f,sy['randbase'],seed.to_bytes(2,'big'))]]+[(chosen+1,sy['world_actor_state'],bytes(384)),(chosen+1,sy['hero_x'],(240<<8).to_bytes(2,'big')),(chosen+1,sy['hero_y'],(144<<8).to_bytes(2,'big'))]
 a,b=pair('projectile16',frames,sw,tw);compare(a,b,frames,[8],'projectile16 lifetime');assert (a/f'ram_{chosen:05}.bin').read_bytes()[0x780]==0x16
 death=next(f for f in sorted(frames) if not (a/f'ram_{f:05}.bin').read_bytes()[0x780])
 data=bytearray(768)
 for d in range(4):
  e=bytearray(48);e[0]=0x16;e[10]=d;e[0x11]=80;e[0x13]=120;data[(8+d)*48:(9+d)*48]=e
 frames=set(range(3102,3210));a,b=pair('four-projectiles',frames,[(3102,0x600,bytes(data)),(3102,0x312,(240<<8).to_bytes(2,'little')),(3102,0x310,(144<<8).to_bytes(2,'little'))],[(3102,sy['world_actor_state'],bytes(data)),(3102,sy['hero_x'],(240<<8).to_bytes(2,'big')),(3102,sy['hero_y'],(144<<8).to_bytes(2,'big'))]);compare(a,b,frames,range(8,12),'projectile16 four directions')
 culls=[dict(slot=s,frame=next(f for f in sorted(frames) if not (a/f'ram_{f:05}.bin').read_bytes()[0x600+s*48])) for s in range(8,12)]
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),deterministic_cases=16,placement_rooms=placements,proximity_terrain_cases=terrain,controlled_decisions=decisions,projectile16_free_frames=108,projectile16_source_birth=chosen,projectile16_source_cull=death,projectile16_four_direction_culls=culls,collision_descriptor_bytes_excluded=[27,28],source_rng_stream_reproduced=False,sprite_overflow_suppression_verified=False,natural_gameplay_verified=False)
 (ROOT/'validation/trap_walker_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Hidden trap placement/proximity/terrain/walking/projectile16 OK',flush=True)
if __name__=='__main__':main()
