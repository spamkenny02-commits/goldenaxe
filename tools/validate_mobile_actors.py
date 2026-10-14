"""Compare deterministic29/2A/2B transitions directly to the SMS core."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
from validate_actor_ai import random_word

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[(t,s,d) for t,states in [(0x29,[2,6,8]),(0x2a,[2,6,8,10,12]),(0x2b,[6,8,10,12])] for s in states for d in range(4)]
 def record(t,s,d):
  e=bytearray(48);e[0]=t;e[1]=s;e[2]=6;e[3]=0x28;e[10]=d;e[11]=3 if s==2 else 0;e[12]=4 if s==2 else 2;e[13]=16
  e[8:10]=bytes.fromhex('fa84' if s==2 else '4886' if t!=0x2b else '2c87')
  e[0x11]=80;e[0x13]=120;e[0x18]=32
  if s==8:e[4]=3;e[0x14:0x18]=bytes.fromhex('00ff0000')
  return e
 sw=[];tw=[];frames=set()
 for batch in range(6):
  f=3102+batch;data=bytearray(768)
  for slot,(t,s,d) in enumerate(cases[batch*8:batch*8+8]):data[slot*48:(slot+1)*48]=record(t,s,d)
  sw.extend([(f,0x600,bytes(data)),(f,0x1600,bytes(1280))]);tw.extend([(f,sy['world_actor_state'],bytes(data)),(f,sy['sms_vram']+0x3800,bytes(1280))]);frames.add(f)
 a=ROOT/'validation/sms-mobile-matrix';b=ROOT/'validation/md-mobile-matrix'
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',3107,a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
  run(ROOT/'gaw-megadrive.bin',3107,b,frames,PRESSES,ram_writes=tw)
 births=0
 for f in sorted(frames):
  src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];md=native(b,f);dst=md[sy['world_actor_state']:sy['world_actor_state']+768]
  for slot in range(16):
   x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
   assert x[:27]+x[29:]==y[:27]+y[29:],(f,slot,'record',x.hex(),y.hex())
   if slot>=8 and x[0]==0x17:births+=1
 assert births==4,('projectile17 births',births)
 # Source chooses random directions; control the native RNG to the observed
 # single choice. This does not reproduce the complete Z80 refresh stream.
 direction_cases=[]
 for t,state,open_map in [(0x29,4,True),(0x2a,4,True),(0x2b,2,True),(0x2b,4,True),(0x29,6,False),(0x2a,6,False)]:
  e=record(t,state,0 if open_map else 3);e[11]=3 if state==2 else 0;data=bytes(e)+bytes(720)
  name=f'{t:02x}-{state}';a=ROOT/f'validation/sms-mobile-direction-{name}';b=ROOT/f'validation/md-mobile-direction-{name}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',3102,a,{3102},[(200,220,0)]+PRESSES,ram_writes=[(3102,0x600,data)]+([(3102,0x1600,bytes(1280))] if open_map else []))
  expected=(a/'ram_03102.bin').read_bytes()[0x600:0x630];assert expected[1] in ([8] if open_map else [6,8])
  seed=next(n for n in range(1,65536) if random_word(n)&3==expected[10])
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'gaw-megadrive.bin',3102,b,{3102},PRESSES,ram_writes=[(3102,sy['world_actor_state'],data),(3102,sy['randbase'],seed.to_bytes(2,'big'))]+([(3102,sy['sms_vram']+0x3800,bytes(1280))] if open_map else []))
  raw=native(b,3102);actual=raw[sy['world_actor_state']:sy['world_actor_state']+48]
  assert actual[:27]+actual[29:]==expected[:27]+expected[29:],('direction',name,actual.hex(),expected.hex())
  direction_cases.append(dict(type=t,state=state,direction=expected[10],native_rng_choice_controlled=True,open_tilemap_controlled=open_map,blocked_initial_direction_tested=not open_map))
 # Follow the new projectile without further actor or projectile injections.
 data=bytearray(768)
 for slot in range(4):data[slot*48:(slot+1)*48]=record(0x2a,10,slot)
 a=ROOT/'validation/sms-mobile-projectile17';b=ROOT/'validation/md-mobile-projectile17';frames=set(range(3102,3201))
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',3200,a,frames,[(200,220,0)]+PRESSES,ram_writes=[(3102,0x600,bytes(data)),(3103,0x600,bytes(384)),(3102,0x312,(32<<8).to_bytes(2,'little'))])
  run(ROOT/'gaw-megadrive.bin',3200,b,frames,PRESSES,ram_writes=[(3102,sy['world_actor_state'],bytes(data)),(3103,sy['world_actor_state'],bytes(384)),(3102,sy['hero_x'],(32<<8).to_bytes(2,'big'))])
 deaths=[];previous=[0x17]*4
 for f in sorted(frames):
  src=(a/f'ram_{f:05}.bin').read_bytes()[0x600:0x900];raw=native(b,f);dst=raw[sy['world_actor_state']:sy['world_actor_state']+768]
  for slot in range(8,12):
   x=src[slot*48:(slot+1)*48];y=dst[slot*48:(slot+1)*48]
   assert x[:27]+x[29:]==y[:27]+y[29:],('projectile17',f,slot,x.hex(),y.hex())
   if previous[slot-8] and not x[0]:deaths.append(dict(frame=f,slot=slot));previous[slot-8]=x[0]
 assert len(deaths)==4,('projectile17 culls',deaths)
 # Find an original refresh-register choice which actually changes terrain.
 # Reinitialize the controlled record/map each frame; no emulator state is
 # compiled into the port. The chosen native RNG value only controls this test.
 frames=set(range(3102,3166));data=bytes(record(0x2b,8,0))+bytes(720);data=bytearray(data);data[4]=0;data[0x14:0x18]=bytes(4);data=bytes(data)
 sw=[v for f in sorted(frames) for v in [(f,0x600,data),(f,0x1600,bytes(1280)),(f,0x1c47,b'\x03')]]
 a=ROOT/'validation/sms-mobile-terrain-search'
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'input/original.sms',3165,a,frames,[(200,220,0)]+PRESSES,ram_writes=sw)
 chosen=next(f for f in sorted(frames) if (a/f'ram_{f:05}.bin').read_bytes()[0x601]==10)
 seed=next(n for n in range(1,65536) if random_word(n)&15==14)
 tw=[v for f in range(3102,chosen+1) for v in [(f,sy['world_actor_state'],data),(f,sy['sms_vram']+0x3800,bytes(1280)),(f,sy['scratch']+0x847,b'\x03'),(f,sy['randbase'],seed.to_bytes(2,'big'))]]
 b=ROOT/'validation/md-mobile-terrain-test'
 with contextlib.redirect_stdout(io.StringIO()):run(ROOT/'gaw-megadrive.bin',chosen,b,{chosen},PRESSES,ram_writes=tw)
 src=(a/f'ram_{chosen:05}.bin').read_bytes();raw=native(b,chosen);dst=raw[sy['world_actor_state']:sy['world_actor_state']+48];expected=src[0x600:0x630]
 assert dst[:27]+dst[29:]==expected[:27]+expected[29:],('terrain actor',dst.hex(),expected.hex())
 assert src[0x1c47]==raw[sy['scratch']+0x847]==0x66
 assert src[0x1600:0x1b00]==raw[sy['sms_vram']+0x3800:sy['sms_vram']+0x3d00],('terrain tilemap patch')
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),deterministic_initial_record_cases=len(cases),source_core_record_comparisons=96,collision_descriptor_bytes_excluded=[27,28],projectile17_four_direction_births_source_exact=births,projectile17_free_motion_compared_frames=99,projectile17_source_culls_exact=deaths,direction_cases=direction_cases,source_rng_stream_reproduced=False,terrain_change_verified=True,terrain_source_frame=chosen,terrain_native_rng_choice_controlled=True,terrain_tilemap_bytes_source_exact=1280,natural_room52_combat_verified=False)
 (ROOT/'validation/mobile_actors_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Mobile actors48 + directions6 + projectile17 + terrain OK',flush=True)
if __name__=='__main__':main()
