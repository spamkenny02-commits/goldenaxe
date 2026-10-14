"""Cold-load four controlled checkpoints; observe real2D placements/shots."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[]
 for room in [0x51,0x62,0x7d,0x7e]:
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   block[0x40b:0x40d]=room.to_bytes(2,'little');block[0x412:0x414]=room.to_bytes(2,'little')
   if md:raw=bytearray([255])*16384;raw[1::2]=block
   else:raw=block
   p=ROOT/f'validation/{name}-fixed-room-{room:02x}.srm';p.write_bytes(raw);births=[];old=[0]*8;positions=set()
   def observe(frame,ram):
    if frame<1350:return
    offset=sy['world_actor_state'] if md else 0x600
    def get(n):return ram[(offset+n)^1] if md else ram[offset+n]
    for slot in range(8):
     if get(slot*48)==0x2d and get(slot*48+1)==2:positions.add((get(slot*48+0x13),get(slot*48+0x11)))
    for slot in range(8):
     t=get((slot+8)*48)
     if t==0x14 and old[slot]!=0x14:births.append((frame,slot+8))
     old[slot]=t
   out=ROOT/f'validation/{name}-fixed-room-{room:02x}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),2300,out,{1500,1800,2100},([] if md else [(200,220,0)])+[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)],sram_in=p,ram_observer=observe)
   assert len(positions)==2 and births,(room,name,'fixed emitters absent',positions,births)
   rows.append(dict(room=room,system=name,positions=sorted(positions),births=births))
  assert rows[-1]['positions']==rows[-2]['positions'],(room,'placement mismatch')
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),rows=rows,ram_mutations=False,controlled_saved_room=True,all_four_exterior_rooms_verified=True,placement_positions_source_exact=True,absolute_firing_timing_exact=False,full_progression_verified=False)
 (ROOT/'validation/fixed_rooms_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Four fixed-shooter cold-load rooms OK; firing timing differs',flush=True)
if __name__=='__main__':main()
