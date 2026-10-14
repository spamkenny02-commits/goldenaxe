"""Buttons trigger original effects: no sound-state or audio-command injection."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll';cases=[]
 for item,command in [(0,0x90),(1,0x99),(4,0x92),(7,0x97)]:
  systems=[]
  for name,md in [('sms',False),('md',True)]:
   items=bytearray(17);items[0]=items[1]=items[4]=items[7]=1
   if md:
    writes=[(2801,sy['world_actor_state'],bytes(768)),(2801,sy['hero_selected_item'],item.to_bytes(2,'big')),(2801,sy['hero_items'],bytes(items)),(2801,sy['hero_weapon_level'],(1).to_bytes(2,'big')),(2801,sy['hero_health'],(16).to_bytes(2,'big')),(2801,sy['hero_magic'],(24).to_bytes(2,'big'))]
   else:writes=[(2801,0x600,bytes(768)),(2801,0xdf,bytes([item])),(2801,0xe0,bytes(items)),(2801,0x318,b'\x10'),(2801,0xdb,b'\x18')]
   events=[];psg={}
   def observe(f,ram):
    if f<2801:return
    n=sy['sound_ram']+15 if md else 0x1e0f;value=ram[n^1] if md else ram[n]
    if value==command:events.append(f)
   folder=ROOT/f'validation/{name}-sfx-hook-{item}'
   with contextlib.redirect_stdout(io.StringIO()):run(ROOT/('gaw-megadrive.bin' if md else 'input/original.sms'),2900,folder,{2801,2805,2830,2900},([] if md else [(200,220,0)])+PRESSES[:8]+[(2804,2808,8)],ram_writes=writes,ram_observer=observe,core=core,psg_observer=lambda f,p:psg.update({f:p}),audio_out=folder/'audio.wav')
   assert events,(name,item,command,'button did not start effect')
   assert any(any(p[n] for n in [3,5,7]) for f,p in psg.items() if events[0]<=f<=events[0]+10),(name,item,'silent PSG')
   systems.append(dict(system=name,first_effect_frame=events[0],audio_file=str((folder/'audio.wav').relative_to(ROOT)),gameplay_setup_writes=True,audio_state_injected=False))
  cases.append(dict(item=item,command=command,systems=systems));print(f'Button action{item}: effect{command:02X} in SMS and MD OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,scope='Four button-triggered actions; controlled equipment, HP, magic and enemies; sound state never injected',all_game_event_hooks_verified=False,full_progression_verified=False)
 (ROOT/'validation/sfx_hooks_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
