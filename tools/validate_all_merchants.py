"""Compare every source merchant table entry and all purchase/refusal variants."""
import argparse,contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_house_dialogue import native

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int);parser.add_argument('--case');args=parser.parse_args()
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
 assets=json.loads((ROOT/'analysis/merchant_assets.json').read_text());towns={r:(m,g) for r,m,g in assets['towns']}
 nodes={r:(x,y) for r,x,y in assets['nodes']};doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors']
 # Controlled stats retain the ordinary source routines and button selection.
 base=dict(selection=0,gold=255,hp=9,cap=24,magic=0,magic_cap=80,keys=0,shield=1,oil=0,feather=0,potion=0)
 fixtures=[(f'town-{r:02x}',r,{}) for r in towns]
 fixtures += [('feather',0x71,dict(selection=1)),('oil',0x55,dict(selection=2)),('heal30',0xf9,dict(selection=1)),('potion100-owned',0x57,dict(potion=1)),('potion40-owned',0x34,dict(potion=1)),('potion40-poor',0x34,dict(gold=39)),('shield-owned',0xf9,dict(shield=2)),('shield-better',0xf9,dict(shield=3)),('heal-full',0x53,dict(hp=24)),('keys-full',0x71,dict(keys=99)),('feather-owned',0x71,dict(selection=1,feather=1)),('oil-owned',0x55,dict(selection=2,oil=1)),('normal-poor',0x55,dict(gold=99)),('magic4',0x23,dict(selection=1)),('magic8',0x23,dict(selection=2)),('magic-clamp',0x23,dict(selection=2,magic=17,magic_cap=24)),('magic-overflow',0x23,dict(selection=2,magic=240,magic_cap=248)),('magic-full',0x23,dict(magic=24,magic_cap=24)),('magic-poor',0x23,dict(gold=19))]
 if args.limit:fixtures=fixtures[:args.limit]
 else:fixtures += [('confirm_cancel_priority',0x94,dict(both=True))]
 if args.case:
  fixtures=[f for f in fixtures if f[0]==args.case];assert fixtures,'Unknown merchant case: '+args.case
 results=[]
 for label,town,override in fixtures:
  stats=base|override;mode,group=towns[town]
  house=next(d['target'] for d in doors if d['room']==town and d['target'] in nodes);x,y=nodes[house];paths=[]
  for name,md in [('sms',False),('md',True)]:
   raw=(ROOT/f'validation/{name}-save-slot-0.srm').read_bytes();logical=bytearray((raw[1::2] if md else raw).ljust(8192,b'\xff'))
   logical[0x40b:0x40d]=town.to_bytes(2,'little');logical[0x412:0x414]=house.to_bytes(2,'little')
   if md:
    raw=bytearray([255])*16384;raw[1::2]=logical
   else:raw=logical
   p=ROOT/f'validation/{name}-all-merchants-fixture.srm';p.write_bytes(raw);paths.append(p)
  inputs=[(920,935,0),(1000,1005,5),(1050,1065,8),(1300,1310,8),(2000,2050,4)]
  inputs += [(2500+n*40,2510+n*40,5) for n in range(stats['selection'])]
  inputs += [(2600,2610,8),(3500,3510,0)]
  if stats.get('both'):inputs.append((2600,2610,0))
  fields=[('hero_gold',0xdd,'gold'),('hero_health',0x318,'hp'),('hero_max_health',0xda,'cap'),('hero_magic',0xdb,'magic'),('hero_max_magic',0xdc,'magic_cap'),('hero_keys',0xde,'keys'),('hero_shield_level',0xf2,'shield')]
  sw=[(1950,0x310,(y<<8).to_bytes(2,'little')+(x<<8).to_bytes(2,'little')),(1950,0x30a,b'\0')]+[(1950,o,bytes([stats[k]])) for _,o,k in fields]
  tw=[(1950,sy[k],v.to_bytes(2,'big')) for k,v in [('hero_x',x<<8),('hero_y',y<<8),('hero_direction',0)]]+[(1950,sy[k],stats[s].to_bytes(2,'big')) for k,_,s in fields]
  for item,key in [(2,'oil'),(9,'feather'),(8,'potion')]:
   sw.append((1950,0xe0+item,bytes([stats[key]])));tw.append((1950,sy['hero_items']+item,bytes([stats[key]])))
  a=ROOT/f'validation/sms-all-merchants-{label}';b=ROOT/f'validation/md-all-merchants-{label}'
  observations=[[],[]]
  def observer(md):
   def observe(frame,raw):
    if not 2600<=frame<=3300:return
    val=int.from_bytes(raw[sy['hero_gold']:sy['hero_gold']+2],'little') if md else raw[0xdd]
    seq=observations[int(md)]
    if not seq or seq[-1][1]!=val:seq.append((frame,val))
   return observe
  with contextlib.redirect_stdout(io.StringIO()):
   run(ROOT/'input/original.sms',3800,a,{1900,2400,3300,3800},[(200,220,0)]+inputs,ram_writes=sw,sram_in=paths[0],ram_observer=observer(False))
   run(ROOT/'gaw-megadrive.bin',3800,b,{1900,2400,3300,3800},inputs,ram_writes=tw,sram_in=paths[1],ram_observer=observer(True))
  def value(d,k):return int.from_bytes(d[sy[k]:sy[k]+2],'big')
  assert value(native(b,2400),'merchant_phase')==1,(label,'not open')
  source=(a/'vram_02400.bin').read_bytes();md=native(b,2400);off=sy['sms_vram']
  assert source[0x2000:0x3040]==md[off+0x2000:off+0x3040],(label,'initial bitmap')
  im=Image.open(a/'frame_02400.png').convert('RGB').crop((0,0,256,160));jm=Image.open(b/'frame_02400.png').convert('RGB').crop((0,16,256,176))
  pal=set(im.getdata());conv={c:min(pal,key=lambda d:sum((u-v)**2 for u,v in zip(c,d))) for c in set(jm.getdata())}
  diff=sum(u!=conv[v] for u,v in zip(im.getdata(),jm.getdata()))
  assert diff==0,(label,'initial panel pixels',diff)
  for f in [3300,3800]:
   sms=(a/f'ram_{f:05}.bin').read_bytes();md=native(b,f)
   for k,o,l in [('game_state',0x1d,1),('room_id',0xb9,2)]+[(k,o,1) for k,o,_ in fields]:
    assert value(md,k)==int.from_bytes(sms[o:o+l],'little'),(label,f,k,value(md,k),int.from_bytes(sms[o:o+l],'little'))
   for item in [2,8,9]:assert md[sy['hero_items']+item]==sms[0xe0+item],(label,f,'item',item)
   if f==3300 and value(md,'merchant_phase'):
    source=(a/f'vram_{f:05}.bin').read_bytes();assert source[0x2000:0x3040]==md[off+0x2000:off+0x3040],(label,'transaction bitmap')
  assert value(md,'merchant_phase')==0,(label,'not closed')
  assert [v for _,v in observations[0]]==[v for _,v in observations[1]],(label,'currency sequence')
  intervals=[[seq[n][0]-seq[n-1][0] for n in range(2,len(seq))] for seq in observations]
  assert intervals[0]==intervals[1],(label,'per-unit payment intervals',set(intervals[0]),set(intervals[1]))
  results.append(dict(name=label,town=town,house=house,mode=mode,stats=stats,initial_panel_pixels_exact=True,prompt_bitmap_bytes_exact=4160,settled_states_source_exact=2,currency_decrements=len(observations[0])-1,currency_intervals_source_exact=True,currency_intervals=list(set(intervals[1])),controlled_interior_checkpoint_and_stats=True))
  print('Merchant',label,'OK',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=results,all_23_towns_checked=args.limit is None and args.case is None,selected_case=args.case,natural_world_access_verified=False,absolute_timing_verified=False)
 (ROOT/(f'validation/all_merchants_case_{args.case}_report.json' if args.case else 'validation/all_merchants_report.json' if args.limit is None else 'validation/all_merchants_partial_report.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
