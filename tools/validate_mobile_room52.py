"""Cold-load the controlled saved state52; leave enemy records untouched."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 load=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)];frames={1400,1500,1600,1700,1800,1900,2100};rows=[];events={}
 for name,md in [('sms',False),('md',True)]:
  out=ROOT/f'validation/{name}-mobile-room52';events[name]={}
  def observe(frame,raw):
   if frame<1350:return
   state=int.from_bytes(raw[sy['game_state']:sy['game_state']+2],'little') if md else raw[0x1d]
   hp=int.from_bytes(raw[sy['hero_health']:sy['hero_health']+2],'little') if md else raw[0x318]
   if state==12 and hp==9:events[name].setdefault('loaded_live_checkpoint',frame)
   if 'loaded_live_checkpoint' in events[name]:
    if hp==0:events[name].setdefault('first_zero_hp_frame',frame)
    if state==20:events[name].setdefault('first_death_state_frame',frame)
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),2100,out,frames,([] if md else [(200,220,0)])+load,sram_in=ROOT/f'validation/{name}-all-save-52-yes.srm',ram_observer=observe)
  for f in sorted(frames):
   raw=native(out,f) if md else (out/f'ram_{f:05}.bin').read_bytes()
   if md:state=int.from_bytes(raw[sy['game_state']:sy['game_state']+2],'big');hp=int.from_bytes(raw[sy['hero_health']:sy['hero_health']+2],'big');actors=raw[sy['world_actor_state']:sy['world_actor_state']+768]
   else:state=raw[0x1d];hp=raw[0x318];actors=raw[0x600:0x900]
   rows.append(dict(system=name,frame=f,state=state,hp=hp,actor_types=[actors[n*48] for n in range(16)],actor_positions=[(actors[n*48+0x13],actors[n*48+0x11]) for n in range(5)]))
  assert rows[-1]['hp']==0 and rows[-1]['state']==20,(name,'enemy contact/death absent')
  assert all(k in events[name] for k in ['first_zero_hp_frame','first_death_state_frame'])
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),controlled_saved_health=9,actor_records_not_cleared=True,ram_mutations=False,rows=rows,events=events,both_versions_enemy_contact_and_death_verified=True,absolute_death_timing_exact=events['sms']==events['md'],full_behavior_fidelity_verified=False)
 (ROOT/'validation/mobile_room52_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(events,indent=2))
if __name__=='__main__':main()
