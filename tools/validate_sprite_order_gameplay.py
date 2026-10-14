"""Source0940 depth/rotating order, count and overflow gate production segments production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x61,f'count-{n}',6,20) for n in [0,1,6,7,8,12]]+[(0x61,'overflow',6,20),(0x61,'hidden-count',6,20),(0x61,'mixed-count',6,20)]
 for region in ['auto','pal']:
  for typ,name,state,span in trials:
   traces={};sats={};mode_traces={};source_clock=[];adjustments=[]
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);number=int(name.split('-')[1]) if name.startswith('count-') else 5 if name in ['mixed-count','overflow'] else 7
    for n in range(number):
     v=memoryview(e)[n*48:n*48+48];v[0]=typ;v[1]=6;v[3]=3;v[6]=255;v[8:10]=bytes.fromhex('4997');v[12]=2;v[13]=16;v[0x11]=32+(n//2)*24;v[0x13]=40+(n%2)*80
     if name=='overflow':v[0x11]=80
     if name=='hidden-count' and n>=2:v[3]=0
    hx,hy=224,144;hxf=0;hc=0;hdx=0;tilemap=bytearray(1280)
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e),(2800,0x1600 if tag=='sms' else sy['sms_vram']+0x3800,tilemap)]
    spell=bytearray(48);loot=bytearray(336)
    if name=='mixed-count':
     spell[0]=3;spell[1]=1;spell[3]=1;spell[4]=100;spell[8:10]=bytes.fromhex('1184');spell[12]=4;spell[13]=1;spell[0x11]=24;spell[0x13]=200
     loot[0]=8;loot[1]=2;loot[2]=0x92;loot[3]=1;loot[5]=127;loot[8:10]=bytes.fromhex('ce84');loot[0x11]=120;loot[0x13]=64
    writes += [(2800,0x330 if tag=='sms' else sy['world_spell_state'],spell),(2800,0x4b0 if tag=='sms' else sy['world_loot_state'],loot)]
    if tag=='sms':writes += [(2800,0x301,b'\x01'),(2800,0x303,bytes([3,hc,0])),(2800,0x310,(hy<<8).to_bytes(2,'little')+((hx<<8)|hxf).to_bytes(2,'little')+bytes(2)+hdx.to_bytes(2,'little'))]
    else:
     for k,value in [('hero_state',1),('hero_flags',3),('hero_counter',hc),('hero_hurt',0),('hero_y',hy<<8),('hero_x',(hx<<8)|hxf),('hero_dy',0),('hero_dx',hdx)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={};sprites={};modes={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes(r[0x310:0x314]);modes[f]=dict(count=r[0x47],overflow=bool(r[0x1b]&64),clock=r[0x2f])
      else:
       def w(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
       rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+w('hero_y').to_bytes(2,'little')+w('hero_x').to_bytes(2,'little');modes[f]=dict(count=w('world_object_tick_count'),overflow=bool(w('world_sms_sprite_overflow')),clock=(int.from_bytes(bytes(r[(sy['vtimer']+i)^1] for i in range(4)),'big')-int.from_bytes(bytes(r[(sy['world_clock_shift']+i)^1] for i in range(4)),'big'))&255)
    def vram(f,v):
     if not 2802<=f<2800+span:return
     entries=[]
     if tag=='sms':
      for n in range(64):
       if v[0x3f00+n]==0xd0:break
       entries.append([v[0x3f00+n],v[0x3f80+n*2],v[0x3f81+n*2]])
     else:
      word=lambda a:int.from_bytes(bytes([v[a^1],v[(a+1)^1]]),'big');n=0
      for count in range(80):
       a=0xf400+n*8;tile=(word(a+4)&0x7ff)-272
       if tile>=0:entries.append([(word(a)-145)&255,(word(a+6)-128)&255,tile])
       n=word(a+2)&127
       if not n:break
     sprites[f]=entries
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/sprite-order-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows;sats[tag]=sprites;mode_traces[tag]=modes
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   assert mode_traces['sms']==mode_traces['md'],(region,name,'C047/IRQ status/clock',mode_traces)
   assert sats['sms']==sats['md'],(region,name,'sprite order',[(f,sats['sms'][f],sats['md'][f]) for f in sats['sms'] if sats['sms'][f]!=sats['md'][f]][:2])
   assert {mode_traces['sms'][f]['clock']&3 for f in sats['sms']}=={0,1,2,3}
   counts=sorted({x['count'] for x in mode_traces['sms'].values()});overflow_phases=sorted({x['clock']&3 for x in mode_traces['sms'].values() if x['overflow']})
   assert counts==[number+1+(2 if name=='mixed-count' else 0)],(region,name,counts)
   if name=='overflow':assert counts==[6] and overflow_phases==[0,1,2,3],(region,name,counts,overflow_phases)
   if name in ['hidden-count','mixed-count']:assert counts==[8]
   cases.append(dict(region=region,type=typ,segment=name,frames=span,sat_frames_exact=18,all_four_phases=True,source_object_counts=counts,source_overflow_phases=overflow_phases,all_768_actor_bytes_and_hero_xy_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Held actors injected before frame2800, hero fixed, controlled collision map, initial world clock aligned. Source C047/native object visit count, IRQ overflow status and clock compare20 frames per case; actual complete SAT compares18 frames after the first two fixture/presentation frames. Counts0/1/6/7/8/12 actors plus hero, overflow layout, hidden nonzero objects and mixed spell/loot/actor slots test the eight-object gate and all four phase windows. No direct status or VRAM writes.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/sprite_order_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
