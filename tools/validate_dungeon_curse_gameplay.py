"""Deterministic53 curse, armor defense and remedy production-loop segments, explicit initial clock alignment."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
 sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))};source=(ROOT/'input/original.sms').read_bytes();cases=[]
 trials=[(0x53,'appearance',2,30,0),(0x53,'walk',8,32,0),(0x53,'curse-flag',8,16,0),(0x53,'curse-contact',8,16,0),(0x53,'remedy-active',8,36,1),(0x53,'remedy-idle',8,36,0)]
 for region in ['auto','pal']:
  for typ,name,state,span,initial_curse in trials:
   traces={};source_clock=[];adjustments=[];crams={}
   for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
    e=bytearray(768);v=memoryview(e)[:48];v[0]=typ;v[1]=state;v[3]=0x2b;v[0x11]=80;v[0x13]=128;v[10]=1;v[0x18:0x1b]=source[0x320ea+(typ-32)*4:0x320ea+(typ-32)*4+3]
    v[8:10]=bytes.fromhex('fa84' if state==2 else 'fb93');v[12]=4 if state==2 else 2;v[13]=10
    if state==8:v[4]=64 if name!='walk' else 32;v[0x14:0x18]=source[0x87d2:0x87d6]
    if name=='curse-flag':v[3]|=4
    if state==8:
     def word(a):return int.from_bytes(source[0x30000+(a&0x3fff):0x30002+(a&0x3fff)],'little')
     desc=word(word(0x93fb+v[10]*2));off=0x30000+(desc&0x3fff);v[0x1b:0x1d]=source[off+1:off+3]
    hx,hy=(128,80) if name=='curse-contact' else (224,144);selected=2 if name.startswith('remedy') else 0
    writes=[(2800,0x600 if tag=='sms' else sy['world_actor_state'],e)]
    if tag=='sms':writes += [(2800,0xbf,bytes([initial_curse])),(2800,0xf1,b'\x03\x02'),(2800,0xe2,b'\x01'),(2800,0xdf,bytes([selected])),(2800,0x301,b'\x01'),(2800,0x310,(hy<<8).to_bytes(2,'little')+(hx<<8).to_bytes(2,'little')+bytes(4))]
    else:
     writes += [(2800,sy['game_save_state']+15,bytes([initial_curse])),(2800,sy['hero_items']+2,b'\x01')]
     for k,value in [('hero_y',hy<<8),('hero_x',hx<<8),('hero_dy',0),('hero_dx',0),('hero_state',1),('hero_armor_level',3),('hero_shield_level',2),('hero_selected_item',selected)]:writes.append((2800,sy[k],value.to_bytes(2,'big')))
    folder=ROOT/f'validation/dungeon-curse-gameplay-{typ:02x}-{name}-{region}-{tag}'
    rows={}
    def observe(f,r):
     if f==2799:
      if tag=='sms':source_clock.append(r[0x2f])
      else:
       read32=lambda k:int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(4)),'big');shift=read32('world_clock_shift');adjustment=((read32('vtimer')-shift)&255)-source_clock[0]
       writes.append((2800,sy['world_clock_shift'],((shift+adjustment)&0xffffffff).to_bytes(4,'big')));adjustments.append(adjustment)
     if 2800<=f<2800+span:
      if tag=='sms':rows[f]=bytes(r[0x600:0x900])+bytes([r[0xbf],r[0x31a],r[0x318],r[0xdf],r[0xe2],r[0x1cb6],r[0x1cb7]])
      else:
       def word(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
       pal=lambda n:word('sms_palette') if False else int.from_bytes(bytes(r[(sy['sms_palette']+n*2+i)^1] for i in range(2)),'big')
       rows[f]=bytes(r[(sy['world_actor_state']+i)^1] for i in range(768))+bytes([r[(sy['game_save_state']+15)^1],word('hero_defense'),word('hero_health'),word('hero_selected_item'),r[(sy['hero_items']+2)^1],pal(22),pal(23)])
    captures=set(range(2800,2800+span))
    inputs=([(200,220,0)] if tag=='sms' else [])+PRESSES[:8]+([(2810,2812,8)] if name.startswith('remedy') else [])
    with contextlib.redirect_stdout(io.StringIO()):run(rom,2800+span,folder,captures,inputs,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
    crams[tag]={f:[int.from_bytes((folder/f'cram_{f:05}.bin').read_bytes()[n*2:n*2+2],'little') for n in [22,23]] for f in captures}
    traces[tag]=rows
   for f in traces['sms']:
    a,b=traces['sms'][f],traces['md'][f];assert a==b,(region,hex(typ),name,f,[(j,x,y) for j,(x,y) in enumerate(zip(a,b)) if x!=y][:24])
   if name in ['curse-flag','curse-contact']:assert traces['md'][2800+span-1][768]==1 and traces['md'][2800+span-1][769]==2
   if name=='curse-contact':assert traces['md'][2800+span-1][770]<24
   if name=='remedy-active':assert traces['md'][2835][768]==0 and traces['md'][2835][771:773]==bytes([0,0])
   if name=='remedy-idle':assert traces['md'][2835][771:773]==bytes([2,1])
   levels=[0,3,5,7]
   for f,pair in crams['sms'].items():
    expected=[levels[c&3]|(levels[(c>>2)&3]<<3)|(levels[(c>>4)&3]<<6) for c in pair]
    assert expected==crams['md'][f],(region,name,f,'actual armor CRAM',pair,expected,crams['md'][f])
   cases.append(dict(region=region,type=typ,segment=name,frames=span,all_768_actor_bytes_curse_defense_hp_selection_ownership_and_palette_exact=True,actual_armor_cram_words_exact=span*2,clock_adjustments=adjustments));print(region,hex(typ),name,span,'actor frames exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=cases,full_game_ported=False,limits=['Controlled actor and hero records in initial exterior; native clock explicitly aligned to source at fixture start.','Production movement, curse contact, cached defense, armor colors and actual CRAM, plus normal-button remedy activation/retention are tested. Controlled armor/shield3/2 and item2 possession; no magic is spent.','Natural room loads, original RNG/global clock, complete framebuffer/SAT/audio and hardware timing remain unproved.'])
 (ROOT/'validation/dungeon_curse_gameplay_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
