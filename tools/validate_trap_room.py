"""Cold checkpointE3 and real movement inputs; no actor/RAM injections."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 rows=[];inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8),(1600,1610,5),(1640,1688,7),(1740,1780,4)]
 for name,md in [('sms',False),('md',True)]:
  raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'));block[0x40b:0x40d]=(0xe3).to_bytes(2,'little');block[0x412:0x414]=(0xe3).to_bytes(2,'little')
  if md:raw=bytearray([255])*16384;raw[1::2]=block
  else:raw=block
  p=ROOT/f'validation/{name}-trap-room-e3.srm';p.write_bytes(raw);states=set();events={};positions=set();hero=[]
  def observe(frame,ram):
   if frame<1350:return
   offset=sy['world_actor_state'] if md else 0x600
   def get(n):return ram[(offset+n)^1] if md else ram[offset+n]
   for slot in range(8):
    if get(slot*48)!=0x35:continue
    state=get(slot*48+1);states.add(state)
    if state==2:positions.add((get(slot*48+0x13),get(slot*48+0x11)))
    if state==4:events.setdefault('first_activation',frame)
    if state==10:events.setdefault('first_walking',frame)
   if frame in [1500,1620,1650,1700]:
    x=int.from_bytes(ram[sy['hero_x']:sy['hero_x']+2],'little')>>8 if md else ram[0x313];y=int.from_bytes(ram[sy['hero_y']:sy['hero_y']+2],'little')>>8 if md else ram[0x311];hero.append((frame,x,y))
  out=ROOT/f'validation/{name}-trap-room-e3'
  with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),2300,out,{1500,1700,1800,2100},([] if md else [(200,220,0)])+inputs,sram_in=p,ram_observer=observe)
  assert 'first_activation' in events and 'first_walking' in events,(name,states,hero)
  rows.append(dict(system=name,room=0xe3,states=sorted(states),events=events,hidden_positions=sorted(positions),hero_positions=hero))
 assert rows[0]['hidden_positions']==rows[1]['hidden_positions']
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),rows=rows,ram_mutations=False,controlled_saved_room=True,real_movement_trigger_verified=True,hidden_positions_source_exact=True,absolute_timing_exact=rows[0]['events']==rows[1]['events'],full_progression_verified=False)
 (ROOT/'validation/trap_room_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Cold-load trap activation through real movement inputs OK',flush=True)
if __name__=='__main__':main()
