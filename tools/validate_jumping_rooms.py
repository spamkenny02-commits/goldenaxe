"""Cold checkpoints23/CD: observe parent/shadow pairs without RAM injections."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[]
 for room,t in [(0x23,0x31),(0xcd,0x32)]:
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   block[0x40b:0x40d]=room.to_bytes(2,'little');block[0x412:0x414]=room.to_bytes(2,'little')
   if md:raw=bytearray([255])*16384;raw[1::2]=block
   else:raw=block
   p=ROOT/f'validation/{name}-jumping-room-{room:02x}.srm';p.write_bytes(raw);events={};checks=[0];states=set()
   def observe(frame,ram):
    if frame<1350:return
    offset=sy['world_actor_state'] if md else 0x600
    def get(n):return ram[(offset+n)^1] if md else ram[offset+n]
    for slot in range(7):
     base=slot*48
     if get(base)!=t:continue
     states.add(get(base+1))
     if get(base+1)>2 and get(base+48)==0x30 and get(base+51)&1:
      assert get(base+0x23)==get(base+48+0x13) and get(base+0x27)==get(base+48+0x11),(name,room,frame,slot,'shadow detached')
      checks[0]+=1;events.setdefault(str(slot),frame)
   out=ROOT/f'validation/{name}-jumping-room-{room:02x}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),2300,out,{1500,1800,2100},([] if md else [(200,220,0)])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=p,ram_observer=observe)
   assert events and 10 in states,(name,room,'jumping actors absent',events,states)
   rows.append(dict(room=room,system=name,type=t,first_shadow_events=events,body_states=sorted(states),attached_shadow_frame_checks=checks[0]))
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),rows=rows,ram_mutations=False,controlled_saved_room=True,two_jumping_types_and_shadows_verified=True,absolute_timing_exact=False,full_progression_verified=False)
 (ROOT/'validation/jumping_rooms_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Two cold-load jumping rooms and attached shadows OK',flush=True)
if __name__=='__main__':main()
