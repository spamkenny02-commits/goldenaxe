"""Cold-load exterior fixtures; exercise every direct door and its standard exit."""
import argparse,contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_house_dialogue import native
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int);parser.add_argument('--mask',type=lambda v:int(v,0));parser.add_argument('--no-exit',action='store_true');args=parser.parse_args()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 ref=json.loads((ROOT/'analysis/doors_reference.json').read_text());rows=ref['direct_unconditional_doors'];results=[]
 if args.limit:rows=rows[:args.limit]
 def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
 for index,door in enumerate(rows):
  room,x,y,target=[door[k] for k in ['room','x','y','target']]
  paths=[]
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();logical=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   logical[0x412:0x414]=room.to_bytes(2,'little')
   if md:
    raw=bytearray([255])*16384;raw[1::2]=logical
   else:raw=logical
   p=ROOT/f'validation/{name}-door-fixture.srm';p.write_bytes(raw);paths.append(p)
  suffix=str(index) if args.mask is None else f'mask-{args.mask:02x}-{index}'
  a=ROOT/f'validation/sms-expanded-door-{suffix}';b=ROOT/f'validation/md-expanded-door-{suffix}'
  inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8)]
  # Set one final one-pixel step into the script coordinate. Room assets were
  # loaded by the ordinary Continue path from a controlled SRAM checkpoint.
  sw=[(1950,0x310,(y<<8).to_bytes(2,'little')+((x-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(1950,0x304,b'\x01'),(1950,0x30a,b'\0'),(1950,0x600,bytes(768))]
  tw=[(1950,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',(x-1)<<8),('hero_y',y<<8),('hero_dy',0),('hero_dx',256),('hero_counter',1),('hero_direction',0)]]+[(1950,sy['world_actor_state'],bytes(768))]
  for f in range(1400,1901,50):
   sw.append((f,0x600,bytes(768)));tw.append((f,sy['world_actor_state'],bytes(768)))
  sw +=[(1900,0x310,(112<<8).to_bytes(2,'little')+(136<<8).to_bytes(2,'little')+bytes(4)),(1900,0x304,b'\x00'),(1900,0x301,b'\x00'),(1900,0x303,b'\x03'),(1900,0x318,b'\x18\x00')]
  tw +=[(1900,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',136<<8),('hero_y',112<<8),('hero_counter',0),('hero_dx',0),('hero_dy',0),('hero_state',0),('hero_health',24),('hero_hurt',0)]]
  if args.mask is not None:
   records=bytearray(768)
   for slot in range(8):
    if args.mask&(128>>slot):
     base=slot*48;records[base]=0x20;records[base+3]=3;records[base+0x11]=16;records[base+0x13]=16;records[base+0x18]=4
   sw.append((1950,0x600,bytes(records)));tw.append((1950,sy['world_actor_state'],bytes(records)))
  has_exit=(target in ref['standard_house_exits']) and not args.no_exit
  if has_exit:
   sw +=[(2400,0x310,(160<<8).to_bytes(2,'little')+(135<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),(2400,0x304,b'\x01'),(2400,0x30a,b'\0')]
   tw +=[(2400,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',135<<8),('hero_y',160<<8),('hero_dy',0),('hero_dx',256),('hero_counter',1),('hero_direction',0)]]
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',2800,a,{1900,2300,2800},[(200,220,0)]+inputs,ram_writes=sw,sram_in=paths[0])
   run(ROOT/'gaw-megadrive.bin',2800,b,{1900,2300,2800},inputs,ram_writes=tw,sram_in=paths[1])
  for frame,expected_room in [(1900,room),(2300,target),(2800,room if has_exit else target)]:
   sms=(a/f'ram_{frame:05}.bin').read_bytes();md=native(b,frame)
   assert value(md,'room_id')==sms[0xb9]==expected_room,(index,door,frame,'room',value(md,'room_id'),sms[0xb9])
   for k,o,l in [('game_state',0x1d,1),('hero_x',0x312,2),('hero_y',0x310,2),('hero_direction',0x30a,1),('hero_health',0x318,1)]:assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(index,door,frame,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
  sms=(a/'ram_02300.bin').read_bytes();md=native(b,2300);mask=md[sy['game_save_state']+0x150+room]
  assert mask==sms[0x200+room],(index,'persisted mask',mask,sms[0x200+room])
  if args.mask is not None:assert mask==args.mask,(index,'living mask',mask,args.mask)
  results.append(dict(persisted_mask_source_exact=mask,**door,entry_states_source_exact=True,standard_exit_source_exact=has_exit,controlled_checkpoint_and_single_step=True))
  print('Door',index,hex(room),'->',hex(target),'OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=results,all_direct_prefix_doors_checked=(len(results)==len(ref['direct_unconditional_doors'])),graphics_and_fade_timing_verified=False,quest_gated_suffixes_ported=False)
 (ROOT/('validation/expanded_doors_report.json' if args.mask is None else f'validation/door_living_mask_{args.mask:02x}_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
