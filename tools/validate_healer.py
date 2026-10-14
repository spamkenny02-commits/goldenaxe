"""First-village free night: life capacity, preserved resources, refusal and fade."""
import contextlib,hashlib,io,json,re,sys
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native
def main():
 pal='--pal' in sys.argv;suffix='-pal' if pal else ''
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
 cases=[]
 for name,hp,cap,choice in [('heal',9,24,'yes'),('capacity48',9,48,'yes'),('already_full',24,24,'yes'),('decline',9,24,'no'),('confirm_down_priority',9,24,'both')]:
  a=ROOT/f'validation/sms-healer-{name}{suffix}';b=ROOT/f'validation/md-healer-{name}{suffix}'
  extra=[(3650,3655,5)] if choice=='no' else [(3700,3710,5)] if choice=='both' else []
  inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3500,4)]+extra+[(3700,3710,8),(4300,4310,8)]
  sw=[(3300,0x310,(88<<8).to_bytes(2,'little')+(216<<8).to_bytes(2,'little')),(3300,0x30a,b'\0'),(3300,0x318,bytes([hp])),(3300,0xda,bytes([cap,11,cap,87]))]
  tw=[(3300,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',216<<8),('hero_y',88<<8),('hero_direction',0),('hero_health',hp),('hero_max_health',cap),('hero_magic',11),('hero_max_magic',cap),('hero_gold',87)]]
  frames={3600,4200,4500}|set(range(3680,3881))|set(range(3340,3451))|set(range(4290,4401))
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',4500,a,frames,[(200,220,0)]+inputs,ram_writes=sw,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
   run(ROOT/'gaw-megadrive.bin',4500,b,frames,inputs,ram_writes=tw,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
  x=Image.open(a/'frame_03600.png').convert('RGB').crop((0,0,256,160));y=Image.open(b/'frame_03600.png').convert('RGB').crop((0,16,256,176))
  pal=set(x.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(y.getdata())}
  assert all(u==conv[v] for u,v in zip(x.getdata(),y.getdata())),(name,'initial service pixels')
  for frame in [4200,4500]:
   sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
   for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_health',0x318,1),('hero_max_health',0xda,1),('hero_magic',0xdb,1),('hero_max_magic',0xdc,1),('hero_gold',0xdd,1),('hero_x',0x312,2),('hero_y',0x310,2)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(name,frame,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
   if frame==4200:
    vram=(a/f'vram_{frame:05}.bin').read_bytes();off=sy['sms_vram'];assert md[off+0x2000:off+0x3040]==vram[0x2000:0x3040],(name,'farewell text tiles')
  assert value(md,'hero_health')==(hp if choice=='no' else cap) and value(md,'healer_phase')==0
  for frame in list(range(3340,3451))+list(range(4290,4401)):
   assert (b/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40,(name,'entry/exit disabled',frame)
   assert Image.open(b/f'frame_{frame:05}.png').convert('RGB').crop((0,176,256,224)).getbbox() is not None
  rest=[frame for frame in range(3680,3881) if not ((b/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40)]
  source_rest=[frame for frame in range(3680,3881) if not ((a/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40)]
  assert rest==source_rest,(name,'night display interval',rest,source_rest)
  assert (len(rest)>=60 if choice!='no' else not rest),(name,'night missing')
  cases.append(dict(name=name,controlled_initial_position_and_stats=True,selection_by_buttons=True,initial_panel_pixels_exact=True,farewell_vram_bytes_exact=4160,settled_fields_exact=2,entry_exit_hud_visible_frames=222,night_display_disabled_frames=len(rest),night_display_interval_source_exact=True,magic_and_gold_preserved=True))
  print('Healer',name,'OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,scope='First village94 free healer/night',absolute_fade_timing_exact=False,paid_villages_checked_by_this_test=False)
 report['region']='pal' if pal else 'auto'
 (ROOT/f'validation/healer{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
