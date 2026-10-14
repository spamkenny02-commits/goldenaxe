"""First-village merchant: source/native purchases, refusals and service restoration."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 cases=[]
 fixtures=[('key',0,255,0,0,0),('feather',1,255,0,0,0),('oil',2,255,0,0,0),('poor',0,0,0,0,0),('keys_full',0,255,99,0,0),('feather_owned',1,255,0,1,0),('oil_owned',2,255,0,0,1)]
 for name,selection,gold,keys,feather,oil in fixtures:
  a=ROOT/f'validation/sms-merchant-{name}';b=ROOT/f'validation/md-merchant-{name}'
  inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3500,4)]+([(3650,3655,5)] if selection>=1 else [])+([(3680,3685,5)] if selection==2 else [])+[(3750,3760,8),(4500,4510,0)]
  sw=[(3300,0x310,(88<<8).to_bytes(2,'little')+(40<<8).to_bytes(2,'little')),(3300,0x30a,b'\0'),(3300,0xdd,bytes([gold,keys])),(3300,0xe9,bytes([feather])),(3300,0xe2,bytes([oil]))]
  tw=[(3300,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',40<<8),('hero_y',88<<8),('hero_direction',0),('hero_gold',gold),('hero_keys',keys)]]+[(3300,sy['hero_items']+9,bytes([feather])),(3300,sy['hero_items']+2,bytes([oil]))]
  frames={3600,4300,4700}|set(range(3340,3451))|set(range(4490,4601))
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',4700,a,frames,[(200,220,0)]+inputs,ram_writes=sw)
   run(ROOT/'gaw-megadrive.bin',4700,b,frames,inputs,ram_writes=tw)
  def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
  md=native(b,3600);assert value(md,'merchant_phase')==1,(name,'merchant not open')
  x=Image.open(a/'frame_03600.png').convert('RGB').crop((0,0,256,160));y=Image.open(b/'frame_03600.png').convert('RGB').crop((0,16,256,176))
  pal=set(x.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(y.getdata())}
  differences=sum(u!=conv[v] for u,v in zip(x.getdata(),y.getdata()))
  assert differences==0,(name,'initial service pixels',differences)
  for frame in [4300,4700]:
   sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
   for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_gold',0xdd,1),('hero_keys',0xde,1),('hero_x',0x312,2),('hero_y',0x310,2)]:
    assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(name,frame,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
   # SMS reuses scratch offsets 17/19 for cursor coordinates after drawing.
   # Compare the 130 rendered tiles in VRAM, unaffected by that record reuse.
   if frame==4300:
    vram=(a/f'vram_{frame:05}.bin').read_bytes();off=sy['sms_vram']
    assert md[off+0x2000:off+0x3040]==vram[0x2000:0x3040],(name,'transaction message VRAM bitmap')
   assert md[sy['hero_items']+2]==sms[0xe2] and md[sy['hero_items']+9]==sms[0xe9],(name,frame,'inventory')
  assert value(md,'merchant_phase')==0 and value(md,'game_state')==12,(name,'service not closed')
  for frame in list(range(3340,3451))+list(range(4490,4601)):
   assert (b/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40,(name,'display disabled',frame)
   assert Image.open(b/f'frame_{frame:05}.png').convert('RGB').crop((0,176,256,224)).getbbox() is not None
  cases.append(dict(name=name,controlled_position_and_initial_stats=True,selection_by_normal_input=True,service_initial_pixels_exact=True,settled_transaction_fields_exact=2,transaction_bitmap_vram_bytes_exact=4160,entry_exit_visible_hud_frames=222))
  print('Merchant',name,'OK',flush=True)
 # Natural route around the furniture, no source/native RAM injections.
 inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3490,6),(3520,3650,4),(3700,3708,7),(3750,3850,4),(4000,4010,8),(4200,4210,0)]
 a=ROOT/'validation/sms-merchant-natural';b=ROOT/'validation/md-merchant-natural'
 with contextlib.redirect_stdout(io.StringIO()):
  run(ROOT/'input/original.sms',4400,a,{3900,4100,4400},[(200,220,0)]+inputs)
  run(ROOT/'gaw-megadrive.bin',4400,b,{3900,4100,4400},inputs)
 for frame in [3900,4100,4400]:
  sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
  for k,o,l in [('game_state',0x1d,1),('hero_x',0x312,2),('hero_y',0x310,2),('hero_gold',0xdd,1)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),('natural merchant',frame,k)
 assert value(native(b,3900),'merchant_phase')==1 and value(md,'merchant_phase')==0
 print('Merchant natural walk/refusal/exit OK',flush=True)
 report=dict(natural_walk_refusal_exit_without_ram_injection=True,md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,scope='First village 94 merchant only; three goods and refusal branches',absolute_transaction_timing_exact=False,other_village_merchants_checked_by_this_test=False,merchant_sound_effects_ported=False)
 (ROOT/'validation/merchant_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
