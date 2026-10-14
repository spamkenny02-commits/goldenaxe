"""Cold-load water rooms without RAM mutations; observe33/34 leap states."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[]
 for room,types in [(0x19,[0x33,0x34]),(0x6a,[0x34]),(0xe9,[0x33])]:
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'));block[0x40b:0x40d]=room.to_bytes(2,'little');block[0x412:0x414]=room.to_bytes(2,'little')
   if md:raw=bytearray([255])*16384;raw[1::2]=block
   else:raw=block
   p=ROOT/f'validation/{name}-water-room-{room:02x}.srm';p.write_bytes(raw);states={t:set() for t in types};events={};births=[];old=[0]*8
   def observe(frame,ram):
    if frame<1350:return
    offset=sy['world_actor_state'] if md else 0x600
    def get(n):return ram[(offset+n)^1] if md else ram[offset+n]
    for slot in range(8):
     t=get(slot*48)
     if t in types:
      state=get(slot*48+1);states[t].add(state)
      if state==16:events.setdefault(str(t),frame)
    for slot in range(8):
     t=get((slot+8)*48)
     if t==0x13 and old[slot]!=0x13:births.append((frame,slot+8))
     old[slot]=t
   out=ROOT/f'validation/{name}-water-room-{room:02x}'
   duration=5000 if room==0x6a else 3000
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),duration,out,{1500,1800,2100,2600},([] if md else [(200,220,0)])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=p,ram_observer=observe)
   # The original34 only walks in the mixed19 fixture before combat stops;
   # its complete leap/shoot cycle is instead observed in its dedicated6A room.
   requirements={t:(8 if room==0x19 and t==0x34 else 16) for t in types}
   assert all(requirements[t] in states[t] for t in types) and births,(room,name,states,births)
   rows.append(dict(room=room,system=name,frames=duration,required_states=requirements,states={str(t):sorted(s) for t,s in states.items()},first_leap_events=events,aimed13_births=births))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),rows=rows,ram_mutations=False,controlled_saved_room=True,three_water_rooms_verified=True,absolute_timing_exact=False,full_progression_verified=False)
 (ROOT/'validation/water_rooms_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Three cold-load water rooms and leaps/shots OK',flush=True)
if __name__=='__main__':main()
