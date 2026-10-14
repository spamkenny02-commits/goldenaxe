"""Original inn table: controlled cold checkpoints, normal service confirmation."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 assets=json.loads((ROOT/'analysis/healer_assets.json').read_text())
 doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors']
 nodes={r:(x,y) for r,x,y in assets['nodes']};results=[]
 fixtures=[(town,cost,'yes',87,9,24) for town,cost in assets['prices']]
 fixtures += [(0x2e,40,'poor',39,9,24),(0x55,20,'no',87,9,24),(0xce,40,'yes',40,48,48)]
 for town,cost,choice,gold,hp,cap in fixtures:
  house=next(d['target'] for d in doors if d['room']==town and d['target'] in nodes)
  x,y=nodes[house];label=f'{town:02x}-{choice}-{gold}-{cap}';paths=[]
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes()
   logical=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   logical[0x40b:0x40d]=town.to_bytes(2,'little');logical[0x412:0x414]=house.to_bytes(2,'little')
   if md:
    raw=bytearray([255])*16384;raw[1::2]=logical
   else:raw=logical
   p=ROOT/f'validation/{name}-paid-healer-fixture.srm';p.write_bytes(raw);paths.append(p)
  inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8),(2000,2050,4)]
  if choice=='no':inputs.append((2500,2510,5))
  inputs += [(2600,2610,8),(3200,3210,8),(3500,3510,8)]
  sw=[(1950,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(1950,0x30a,b'\0'),(1950,0x318,bytes([hp])),(1950,0xda,bytes([cap,11,cap,gold]))]
  tw=[(1950,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',x<<8),('hero_y',y<<8),('hero_direction',0),('hero_health',hp),('hero_max_health',cap),('hero_magic',11),('hero_max_magic',cap),('hero_gold',gold)]]
  a=ROOT/f'validation/sms-paid-healer-{label}';b=ROOT/f'validation/md-paid-healer-{label}'
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',3800,a,{1900,2400,3100,3400,3800},[(200,220,0)]+inputs,ram_writes=sw,sram_in=paths[0])
   run(ROOT/'gaw-megadrive.bin',3800,b,{1900,2400,3100,3400,3800},inputs,ram_writes=tw,sram_in=paths[1])
  def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
  assert value(native(b,2400),'healer_phase')==1,(label,'not open')
  source=(a/'vram_02400.bin').read_bytes();md=native(b,2400);off=sy['sms_vram']
  assert source[0x2000:0x3040]==md[off+0x2000:off+0x3040],(label,'initial prompt bitmap')
  # Portrait and window pixels, with the native palette normalized to SMS.
  im=Image.open(a/'frame_02400.png').convert('RGB').crop((0,0,256,160))
  jm=Image.open(b/'frame_02400.png').convert('RGB').crop((0,16,256,176))
  pal=set(im.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(jm.getdata())}
  diff=sum(u!=conv[v] for u,v in zip(im.getdata(),jm.getdata()))
  assert diff==0,(label,'initial panel pixels',diff)
  for f in [3100,3400,3800]:
   sms=(a/f'ram_{f:05}.bin').read_bytes();md=native(b,f)
   for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_health',0x318,1),('hero_max_health',0xda,1),('hero_magic',0xdb,1),('hero_max_magic',0xdc,1),('hero_gold',0xdd,1)]:
    assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(label,f,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
  assert value(md,'hero_gold')==gold-(cost if choice=='yes' else 0)
  assert value(md,'hero_health')==(cap if choice=='yes' else hp) and value(md,'healer_phase')==0
  results.append(dict(town=town,house=house,cost=cost,choice=choice,initial_gold=gold,health=hp,capacity=cap,prompt_bitmap_exact_bytes=4160,initial_panel_pixels_exact=True,settled_fields_source_exact=3,controlled_interior_checkpoint_and_stats=True))
  print('Inn',label,'OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=results,all_eleven_price_table_towns_checked=True,absolute_timing_checked=False,natural_world_access_checked=False)
 (ROOT/'validation/paid_healer_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
