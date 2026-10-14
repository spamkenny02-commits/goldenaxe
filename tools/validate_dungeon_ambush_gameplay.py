"""Deterministic52 floor trigger, emergence and pauses production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x52,'appearance',4,16,24),(0x52,'emerge-to-aim',4,32,24),(0x52,'pause',10,73,24),(0x52,'contact',8,12,24)]
 for vector in range(8):trials.append((0x52,f'vector-{vector}',8,32,24))
 for magic in [0,7,8,24]:trials.append((0x52,f'flag-{magic}',10,1,magic))
 for name,span in [('floor-blocked',8),('floor-left',1),('floor-right',1),('floor-cross',1)]:trials.append((0x52,name,0,span,24))
 for region in ['auto','pal']:
  for typ,name,state,span,magic in trials:
   traces={};source_clock=[];adjustments=[];cross_hero={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48];v[0]=typ;v[1]=state;v[3]=0x2b;v[0x11]=80;v[0x13]=128;v[10]=1;v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('4593' if state==4 else '6b93');v[12]=3 if state==4 else 2;v[13]=8 if state==4 else 4
    if state==8:v[4]=32
    if state==10:v[4]=72
    if name=='emerge-to-aim':v[11]=2
    if name.startswith('vector') or name=='contact':
     vector=int(name.split('-')[1]) if name.startswith('vector') else 0;start=0x9f61+vector*4;v[0x16:0x18]=source[start:start+2];v[0x14:0x16]=source[start+2:start+4];v[10]=source[0x3f4f+vector]
    if name.startswith('flag'):v[3]|=4
    if state in [8,10]:
     def word(a):return int.from_bytes(source[0x30000+(a&0x3fff):0x30002+(a&0x3fff)],'little')
     desc=word(word(0x936b+v[10]*2));off=0x30000+(desc&0x3fff);v[0x1b:0x1d]=source[off+1:off+3]
    if not state:v[3]=0x28;v[8:10]=bytes(2);v[11]=v[12]=v[13]=0
    hx,hy=(128,80) if name=='contact' else (235,144) if name=='floor-cross' else (224,144);writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0xdb,bytes([magic])),(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     for k,value in [('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0),('hero_magic',magic)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    if name.startswith('floor'):
     offset=(((hy-12)&248)*8)+(((hx-12)>>2)&62);base=0x1600 if tag=='sms' else sy['sms_vram']+0x3800
     for rr in range(3):
      for cc in range(4):writes.append((2800,base+offset+rr*64+cc*2+1,b'\0'))
     writes += [(2800,base+offset+66,bytes([0 if name=='floor-left' else 1])),(2800,base+offset+68,bytes([0 if name=='floor-right' else 1]))]
     if name=='floor-cross':
      writes.append((2800,base+offset+70,b'\0'))
      if tag=='sms':writes += [(2800,0x312,((hx<<8)|255).to_bytes(2,'little')),(2800,0x301,b'\x01'),(2800,0x303,b'\x03\x04'),(2800,0x30a,b'\x03'),(2800,0x316,(256).to_bytes(2,'little'))]
      else:
       for k,value in [('hero_x',(hx<<8)|255),('hero_state',1),('hero_flags',3),('hero_counter',4),('hero_direction',3),('hero_dx',256)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    rows={}
    def observe(f,r):
     if f==2800 and name=='floor-cross':
      cross_hero[tag]=int.from_bytes(r[0x312:0x314],'little') if tag=='sms' else int.from_bytes(bytes(r[(sy['hero_x']+i)^1] for i in range(2)),'big')
      if tag=='sms':assert r[0x52] and r[0x54]
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+int(r[0xdb]).to_bytes(2,'big')+int(r[0x318]).to_bytes(2,'big')
      else:rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+bytes(r[(sy['hero_magic']+i)^1] for i in range(2))+bytes(r[(sy['hero_health']+i)^1] for i in range(2))
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,ROOT/f'validation/dungeon-ambush-gameplay-{typ:02x}-{name}-{region}-{tag}',{2800,2820,2840},([(200,220,0)] if tag=='sms' else [])+PRESSES[:8],ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name.startswith('flag'):assert int.from_bytes(traces['md'][2800][768:770],'big')==max(0,magic-8)
   if name=='contact':assert int.from_bytes(traces['md'][2803][768:770],'big')==16 and int.from_bytes(traces['md'][2803][770:772],'big')<24
   if name=='floor-blocked':assert all(r[1]==0 for r in traces['md'].values())
   if name in ['floor-left','floor-right']:assert traces['md'][2800][1]==2
   if name=='floor-cross':assert cross_hero['sms']==cross_hero['md'] and (cross_hero['sms']>>8)>=236 and traces['md'][2800][1]==0
   if name=='pause':assert traces['md'][2872][1]==6
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_magic_and_hero_health_exact=True,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production actor loop, timer, integration, animation, cached-floor trigger and magic drain execute unchanged. Floor-cross fixture starts a walking hero at235.FF and verifies activation uses pre-movement cache despite crossing236. Appearance/aim/pause and eight vectors tested before random choices.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_ambush_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
