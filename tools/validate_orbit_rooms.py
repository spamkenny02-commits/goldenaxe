"""Cold-load rooms1D/2D; observe42 orbit and homing1C shots."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[]
 for room,types in [(0x1d,[0x42]),(0x2d,[0x42])]:
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'));block[0x40b:0x40d]=room.to_bytes(2,'little');block[0x412:0x414]=room.to_bytes(2,'little')
   block[0x429]=block[0x42a]=80 # Matched test checkpoint health; no ROM balance change.
   if md:raw=bytearray([255])*16384;raw[1::2]=block
   else:raw=block
   p=ROOT/f'validation/{name}-orbit42-room-{room:02x}.srm';p.write_bytes(raw);states={t:set() for t in types};events={};births=[];old=[0]*8
   def observe(frame,ram):
    if frame<1350:return
    offset=sy['world_actor_state'] if md else 0x600
    def get(n):return ram[(offset+n)^1] if md else ram[offset+n]
    for slot in range(8):
     t=get(slot*48)
     if t in types:
      state=get(slot*48+1);states[t].add(state)
      if state==6:events.setdefault(str(t),frame)
    for slot in range(8):
     t=get((slot+8)*48)
     if t==0x1c and old[slot]!=t:births.append((frame,slot+8))
     old[slot]=t
   out=ROOT/f'validation/{name}-orbit42-room-{room:02x}'
   duration=6000
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),duration,out,{1500,1800,2100,2600},([] if md else [(200,220,0)])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=p,ram_observer=observe)
   requirements={t:4 for t in types}
   assert all(requirements[t] in states[t] for t in types) and births,(room,name,states,births)
   rows.append(dict(room=room,system=name,frames=duration,required_states=requirements,states={str(t):sorted(s) for t,s in states.items()},first_walking_events=events,projectile_births=births))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),rows=rows,ram_mutations=False,controlled_saved_room=True,checkpoint_health=80,two_orbit_rooms_verified=True,absolute_timing_exact=False,full_progression_verified=False)
 (ROOT/'validation/orbit_rooms_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Two cold-load orbit42 rooms and shots OK',flush=True)
if __name__=='__main__':main()
