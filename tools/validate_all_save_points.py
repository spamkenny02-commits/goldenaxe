"""All unconditional save nodes: original payload, UI and cold-load checkpoint."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_house_dialogue import native

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 assets=json.loads((ROOT/'analysis/save_assets.json').read_text());nodes={r:(x,y) for r,x,y in assets['nodes']}
 doors=[d for d in json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors'] if d['target'] in nodes]
 inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8),(2000,2050,4)]
 baseline={name:(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes() for name in ['sms','md']}
 def logical(p,md):
  raw=p.read_bytes();return (raw[1::2] if md else raw).ljust(8192,b'\xff')
 def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
 results=[]
 fixtures=[(d,'yes') for d in doors]+[(doors[0],'no'),(doors[0],'cancel'),(doors[0],'both')]
 for door,choice in fixtures:
  town,house=door['room'],door['target'];x,y=nodes[house];label=f'{town:02x}-{choice}';paths=[];outs=[]
  presses=inputs+([(2500,2510,5)] if choice=='no' else [])+[(2600,2610,8)]
  presses+=([(2800,2810,0)] if choice=='cancel' else [(2800,2810,8),(3100,3110,8)])
  if choice=='both':presses.append((2800,2810,0))
  for name,md in [('sms',False),('md',True)]:
   raw=baseline[name];block=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   block[0x40b:0x40d]=town.to_bytes(2,'little');block[0x40d:0x40f]=bytes([door['y'],door['x']]);block[0x412:0x414]=house.to_bytes(2,'little')
   if md:
    raw=bytearray([255])*16384;raw[1::2]=block
   else:raw=block
   p=ROOT/f'validation/{name}-all-save-fixture.srm';p.write_bytes(raw);paths.append(p);outs.append(ROOT/f'validation/{name}-all-save-{label}.srm')
  a=ROOT/f'validation/sms-all-save-{label}';b=ROOT/f'validation/md-all-save-{label}'
  sw=[(1950,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(1950,0x30a,b'\0'),(1950,0x318,b'\x09'),(1950,0xda,bytes([48,11,48,87,5]))]
  tw=[(1950,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',x<<8),('hero_y',y<<8),('hero_direction',0),('hero_health',9),('hero_max_health',48),('hero_magic',11),('hero_max_magic',48),('hero_gold',87),('hero_keys',5)]]
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',3400,a,{2400,2750,3000,3400},[(200,220,0)]+presses,ram_writes=sw,sram_in=paths[0],sram_out=outs[0])
   run(ROOT/'gaw-megadrive.bin',3400,b,{2400,2750,3000,3400},presses,ram_writes=tw,sram_in=paths[1],sram_out=outs[1])
  for f in ([2400,2750] if choice!='no' else [2400]):
   im=Image.open(a/f'frame_{f:05}.png').convert('RGB').crop((0,0,256,160));jm=Image.open(b/f'frame_{f:05}.png').convert('RGB').crop((0,16,256,176))
   pal=set(im.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(jm.getdata())}
   assert all(u==conv[v] for u,v in zip(im.getdata(),jm.getdata())),(label,f,'save UI pixels')
  src,dst=logical(outs[0],False),logical(outs[1],True)
  assert src[0x400:0x650]==dst[0x400:0x650],(label,'payload',[(hex(n),u,v) for n,(u,v) in enumerate(zip(src[0x400:0x650],dst[0x400:0x650])) if u!=v][:20])
  if choice in ['no','cancel']:
   # The SMS also writes upper SRAM outside its three persisted slot records.
   # Compare the metadata and record area, excluding the upper region.
   assert src[:0x1000]==logical(paths[0],False)[:0x1000] and dst[:0x1000]==logical(paths[1],True)[:0x1000],(label,'refusal modified save records')
  else:
   assert int.from_bytes(src[0x412:0x414],'little')==town and src[0x429]==9,(label,'checkpoint')
   aa=ROOT/f'validation/sms-all-save-reload-{label}';bb=ROOT/f'validation/md-all-save-reload-{label}'
   # Isolate checkpoint restoration from combat differences in later rooms.
   clear_source=[(f,0x600,bytes(768)) for f in range(1350,1921,10)]
   clear_native=[(f,sy['world_actor_state'],bytes(768)) for f in range(1350,1921,10)]
   with contextlib.redirect_stdout(io.StringIO()):
    run(ROOT/'input/original.sms',1920,aa,{1900,1920},[(200,220,0)]+inputs[:4],sram_in=outs[0],ram_writes=clear_source)
    run(ROOT/'gaw-megadrive.bin',1920,bb,{1900,1920},inputs[:4],sram_in=outs[1],ram_writes=clear_native)
   for f in [1900,1920]:
    sms=(aa/f'ram_{f:05}.bin').read_bytes();md=native(bb,f)
    for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2),('hero_x',0x312,2),('hero_y',0x310,2),('hero_health',0x318,1),('hero_max_health',0xda,1),('hero_magic',0xdb,1),('hero_max_magic',0xdc,1),('hero_gold',0xdd,1),('hero_keys',0xde,1)]:
     assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(label,f,'reload',k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
    assert value(md,'room_id')==town
  sms=(a/'ram_03400.bin').read_bytes();md=native(b,3400)
  assert value(md,'game_state')==sms[0x1d]==12 and value(md,'room_id')==sms[0xb9]==house
  results.append(dict(town=town,house=house,choice=choice,payload_bytes_source_exact=592,cold_checkpoint_fields_source_exact=choice in ['yes','both'],cold_load_actor_records_cleared=choice in ['yes','both'],ui_pixels_source_exact=True,controlled_interior_checkpoint_and_stats=True))
  print('Save',label,'OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=results,all_four_unconditional_save_nodes_checked=True,all_fourteen_direct_door_locations_checked=True,natural_world_access_verified=False,absolute_timing_verified=False)
 (ROOT/'validation/all_save_points_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
