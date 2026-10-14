"""Source/native three-slot save and cold-boot Continue; original 250h payload."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
ROUTE=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3500,4)]

def native(folder,frame):
 r=(folder/f'ram_{frame:05}.bin').read_bytes()
 return bytes(v for n in range(0,len(r),2) for v in(r[n+1],r[n]))

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
 def sram(path,md):
  r=path.read_bytes();return (r[1::2] if md else r).ljust(8192,b'\xff')
 def image_diff(a,b,f):
  x=Image.open(a/f'frame_{f:05}.png').convert('RGB').crop((0,0,256,160));y=Image.open(b/f'frame_{f:05}.png').convert('RGB').crop((0,16,256,176));pal=set(x.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(y.getdata())}
  return sum(u!=conv[v] for u,v in zip(x.getdata(),y.getdata()))
 for slot in range(3):
  a=ROOT/f'validation/sms-save-slot-{slot}';b=ROOT/f'validation/md-save-slot-{slot}';asram=ROOT/f'validation/sms-save-slot-{slot}.srm';bsram=ROOT/f'validation/md-save-slot-{slot}.srm'
  inputs=ROUTE+[(3700,3710,8)]+([(3820,3825,5)] if slot>=1 else [])+([(3860,3865,5)] if slot==2 else [])+[(3900,3910,8),(4200,4210,8)]
  sw=[];tw=[]
  if slot==2:
   sw=[(3340,0x318,b'\x09'),(3340,0xda,bytes([48,11,48,87,5])),(3340,0xe4,b'\x01'),(3340,0xc6,b'\x02')]
   tw=[(3340,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_health',9),('hero_max_health',48),('hero_magic',11),('hero_max_magic',48),('hero_gold',87),('hero_keys',5),('hero_fire_charge',2)]]+[(3340,sy['hero_items']+4,b'\x01')]
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',4400,a,set(range(3340,3451))|set(range(4190,4301))|{3600,3840,3880,4300,4400},[(200,220,0)]+inputs,ram_writes=sw,sram_out=asram)
   run(ROOT/'gaw-megadrive.bin',4400,b,set(range(3340,3451))|set(range(4190,4301))|{3600,3840,3880,4300,4400},inputs,ram_writes=tw,sram_out=bsram)
  src=sram(asram,False);dst=sram(bsram,True);base=0x400+slot*0x400
  assert src[base:base+0x250]==dst[base:base+0x250],('save payload',slot,[(hex(n),u,v) for n,(u,v) in enumerate(zip(src[base:base+0x250],dst[base:base+0x250])) if u!=v][:20])
  assert src[0x30]==dst[0x30]==slot+1
  assert image_diff(a,b,3600)==0,('save prompt pixels',slot,image_diff(a,b,3600))
  for frame in [3840,3880]:
   sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
   assert value(md,'save_slot_selection')==sms[0xa0],('slot cursor selection',slot,frame)
   assert image_diff(a,b,frame)==0,('slot cursor pixels',slot,frame,image_diff(a,b,frame))
  for frame in range(3340,3451):
   assert (b/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40,('save entry display disabled',slot,frame)
  for frame in range(4190,4301):
   assert (b/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40,('save exit display disabled',slot,frame)
  assert value(native(b,4400),'game_state')==12 and value(native(b,4400),'room_id')==0
  # Load persisted SRAM into a fresh emulator invocation, using normal menu inputs.
  aa=ROOT/f'validation/sms-save-reload-{slot}';bb=ROOT/f'validation/md-save-reload-{slot}';load=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)]
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',1920,aa,set(range(1900,1921)),[(200,220,0)]+load,sram_in=asram)
   run(ROOT/'gaw-megadrive.bin',1920,bb,set(range(1900,1921)),load,sram_in=bsram)
  for frame in range(1900,1921):
   sms=(aa/f'ram_{frame:05}.bin').read_bytes();md=native(bb,frame)
   for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_x',0x312,2),('hero_y',0x310,2),('hero_direction',0x30a,1),('hero_health',0x318,1),('hero_magic',0xdb,1),('hero_gold',0xdd,1),('hero_keys',0xde,1),('hero_max_health',0xda,1),('hero_max_magic',0xdc,1),('hero_fire_charge',0xc6,1)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),('reload field',slot,frame,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
   off=sy['hero_items'];assert md[off:off+17]==sms[0xe0:0xf1],('reload items',slot,frame)
   off=sy['sms_vram'];assert md[off+0x3800:off+0x3d00]==sms[0x1600:0x1b00],('reload map',slot,frame)
  cases.append(dict(slot=slot+1,payload_bytes_exact=592,prompt_playfield_image_exact=True,slot_selection_images_exact=2,entry_frames_display_enabled=111,exit_frames_display_enabled=111,cold_boot_fields_and_map_frames_exact=21,controlled_initial_stats=slot==2,save_load_reached_by_normal_input=True))
  print('Save/cold load slot',slot+1,'OK')
 # Death Continue after cold load uses the saved village checkpoint, not room95.
 a=ROOT/'validation/sms-save-death-reload';b=ROOT/'validation/md-save-death-reload'
 inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8),(2500,2510,8)]
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',3000,a,{2900,3000},[(200,220,0)]+inputs,sram_in=ROOT/'validation/sms-save-slot-2.srm',ram_writes=[(1940,0x318,bytes(1)),(1940,0x600,bytes(768))])
  run(ROOT/'gaw-megadrive.bin',3000,b,{2900,3000},inputs,sram_in=ROOT/'validation/md-save-slot-2.srm',ram_writes=[(1940,sy['hero_health'],bytes(2)),(1940,sy['world_actor_state'],bytes(768))])
 for frame in [2900,3000]:
  sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
  for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_x',0x312,2),('hero_y',0x310,2),('hero_health',0x318,1),('hero_magic',0xdb,1),('hero_gold',0xdd,1)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),('saved death Continue',frame,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
 assert value(md,'room_id')==0x94 and value(md,'hero_health')==24 and value(md,'hero_gold')==63
 # No and explicit cancel must not create a save record.
 cancels=[]
 for label,extra in [('no',[(3650,3655,5),(3700,3710,8),(4000,4010,8)]),('cancel',[(3700,3710,8),(3850,3860,0)])]:
  for kind,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
   folder=ROOT/f'validation/{kind}-save-{label}';sr=ROOT/f'validation/{kind}-save-{label}.srm'
   with contextlib.redirect_stdout(io.StringIO()):run(rom,4200,folder,{4200},([(200,220,0)] if kind=='sms' else [])+ROUTE+extra,sram_out=sr)
   assert sram(sr,kind=='md')[0x400] in (0,255),(label,kind,'unexpected save')
   d=native(folder,4200) if kind=='md' else (folder/'ram_04200.bin').read_bytes()
   assert (value(d,'game_state') if kind=='md' else d[0x1d])==12,(label,kind,'not returned')
  cancels.append(label)
 # A new save overwrites one chosen slot and leaves the existing third slot intact.
 a=ROOT/'validation/sms-save-overwrite';b=ROOT/'validation/md-save-overwrite'
 srcin=ROOT/'validation/sms-save-slot-2.srm';dstin=ROOT/'validation/md-save-slot-2.srm';srcout=ROOT/'validation/sms-save-overwrite.srm';dstout=ROOT/'validation/md-save-overwrite.srm'
 inputs=ROUTE+[(1000,1005,4),(3700,3710,8),(3820,3825,4),(3900,3910,8),(4200,4210,8)]
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',4400,a,{4400},[(200,220,0)]+inputs,sram_in=srcin,sram_out=srcout)
  run(ROOT/'gaw-megadrive.bin',4400,b,{4400},inputs,sram_in=dstin,sram_out=dstout)
 src=sram(srcout,False);dst=sram(dstout,True)
 assert src[0x30]==dst[0x30]==2
 assert src[0x800:0xa50]==dst[0x800:0xa50]
 assert src[0xc00:0xe50]==sram(srcin,False)[0xc00:0xe50]
 assert dst[0xc00:0xe50]==sram(dstin,True)[0xc00:0xe50]
 # Overwrite the occupied third slot with the fresh game's state.
 a=ROOT/'validation/sms-save-overwrite-occupied';b=ROOT/'validation/md-save-overwrite-occupied'
 srcout=ROOT/'validation/sms-save-overwrite-occupied.srm';dstout=ROOT/'validation/md-save-overwrite-occupied.srm'
 inputs=ROUTE+[(1000,1005,4),(3700,3710,8),(3900,3910,8),(4200,4210,8)]
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',4400,a,{4400},[(200,220,0)]+inputs,sram_in=srcin,sram_out=srcout)
  run(ROOT/'gaw-megadrive.bin',4400,b,{4400},inputs,sram_in=dstin,sram_out=dstout)
 src=sram(srcout,False);dst=sram(dstout,True)
 assert src[0x30]==dst[0x30]==3
 assert src[0xc00:0xe50]==dst[0xc00:0xe50] and src[0xc29]==24 and src[0xc2d]==0
 assert src[0xc00:0xe50]!=sram(srcin,False)[0xc00:0xe50]
 for base in [0x400,0x800]:
  assert src[base:base+0x250]==sram(srcin,False)[base:base+0x250]
  assert dst[base:base+0x250]==sram(dstin,True)[base:base+0x250]
 # Empty Continue refuses the empty slot and returns to the main menu on cancel.
 inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1200,1205,4),(1230,1235,4),(1260,1265,4),(1300,1310,8),(1400,1410,0)]
 for kind,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
  folder=ROOT/f'validation/{kind}-continue-empty'
  with contextlib.redirect_stdout(io.StringIO()):run(rom,1500,folder,{1350,1500},([(200,220,0)] if kind=='sms' else [])+inputs)
  if kind=='md':
   d=native(folder,1350);assert value(d,'save_service_phase')==4 and value(d,'game_state')==0
   d=native(folder,1500);assert value(d,'save_service_phase')==0 and value(d,'menu_selection')==0
  else:
   assert (folder/'ram_01350.bin').read_bytes()[0x1d]==0
   assert (folder/'ram_01500.bin').read_bytes()[0xa0]==0
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,cancellation_cases=cancels,death_continue_saved_checkpoint_verified=True,overwrite_preserves_other_slot=True,occupied_slot_overwrite_verified=True,empty_continue_and_cancel_verified=True,absolute_ui_timing_exact=False,other_villages_and_unported_progression_fields_verified=False,scope='Village94 save service, three slots, native SRAM, source-layout records, cold Continue')
 (ROOT/'validation/save_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
