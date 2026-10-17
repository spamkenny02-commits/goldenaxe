"""Original changed-bank prefix16D0..1706 across exterior/house/dungeon classes."""
import contextlib,ctypes as c,hashlib,io,json,os,struct,subprocess
from actor_reference import ROOT
from run_core import run
from validate_native_graphics_prefix import MODULES,WRAPPER
from validate_native_patterns import decode
ROOMS=[0,15,16,79,149,256,496]
ROWS=[(room,r) for room in ROOMS for r in [0,127,128,255]]

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes())+bytearray(0xc0000);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jump(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f3ed5631f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bf3e20d3bf3e81d3bf2100802206c0')
 label('case');emit('f3af3202c03211c0322ec03e023230c03eff3266c03e2032ffffdbbf2a06c07e32b9c0237e32bac0237eed4fcdd016f33e013202c00603')
 label('hold');emit('dbbfe680');jump('ca','hold');emit('05');jump('c2','hold')
 emit('2a00c0232200c001'+len(ROWS).to_bytes(2,'little').hex()+'b7ed42');jump('ca','done')
 emit('2a06c0112000192206c0');jump('c3','case')
 label('done');emit('af3202c03e013204c0');label('halt');jump('c3','halt')
 for at,name in fix:code[at:at+2]=labels[name].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code;image[0x1706]=0xc9
 image[0x80000:0x80000+32*len(ROWS)]=b''.join(room.to_bytes(2,'little')+bytes([r])+bytes(29) for room,r in ROWS)
 original=(ROOT/'input/original.sms').read_bytes();assert image[0x16d0:0x1706]==original[0x16d0:0x1706] and image[0x175f:0x1780]==original[0x175f:0x1780] and image[0x32a:0x3f0]==original[0x32a:0x3f0]
 base=ROOT/'validation/graphics-classes-prefix';base.mkdir(exist_ok=True);fixture=base/'source.sms';fixture.write_bytes(image);return base,fixture

def compile_helper(base):
 wrapper=WRAPPER.replace('graphics_prefix_case(','graphics_class_case(').replace('u16 tile_count','u16 tile_count,u16 room').replace('source_graphics_prefix_class0(&clock,&ctx,patterns,pixels,&end)','source_graphics_prefix_changed(&clock,&ctx,room,patterns,pixels,&end,0)').replace('events[16][6]','events[64][6]').replace('>=16','>=64').replace('>16','>64')
 wrapper=wrapper.replace('u32 *out,u32 *events)','u32 *out,u32 *events,u8 *pixel_output)').replace('return 1;\n}', 'for(n=0;n<16384;n++) pixel_output[n]=pixels[n];\n return 1;\n}')
 (base/'wrapper.c').write_text(wrapper);sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(base/'wrapper.c')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in MODULES]+['-o',str(base/'prefix.dll')]
 built=subprocess.run(args,env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
 dll=c.CDLL(str(base/'prefix.dll'));fn=dll.graphics_class_case;fn.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,*([c.POINTER(c.c_uint8)]*5),c.c_uint16,c.c_uint16,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint8)];fn.restype=c.c_uint8;return dll,fn

def main():
 base,fixture=generate();native,fn=compile_helper(base);rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000])
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_graphicsprefixrefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_foreground_phase_samples','gaw_audio_irq_count']:getattr(dll,name).restype=c.c_uint
 for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_audio_irq_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 cases=[];summaries=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();observed={};checked={};records=[];previous=[0];done=[];vram={}
  def observe(frame,ram):
   case=int.from_bytes(ram[:2],'little');count=dll.gaw_foreground_phase_samples()
   raw=c.string_at(dll.gaw_foreground_phase_events(),count*800);meta=c.string_at(dll.gaw_foreground_m1_events(),count*16)
   for n in range(previous[0],count):
    data=raw[n*800:(n+1)*800];pc,time=struct.unpack_from('<2Q',data);m1,r,_=struct.unpack_from('<Q2I',meta,n*16)
    row=dict(pc=pc,time=time,m1=m1,refresh=r,phase=list(struct.unpack_from('<12I',data,16)),ram=list(data[64:400]),audio=list(data[400:800]))
    records.append(row)
    if pc==0x16d0:observed[case]=[row]
    elif pc==0x1706:observed[case].append(row)
   previous[0]=count
   if ram[2] and case not in checked:checked[case]=frame
   if ram[4]:done.append(frame)
  def video(frame,raw):
   for case,f in checked.items():
    if f==frame:vram[case]=bytes(raw[:16384])
  with contextlib.redirect_stdout(io.StringIO()):run(fixture,4000,base/region,set(),[],skip_intro=False,core=core,ram_observer=observe,vram_observer=video,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
  assert done and len(observed)==len(checked)==len(vram)==len(ROWS),(region,len(observed),len(checked),len(vram))
  (base/(region+'-records.json')).write_text(json.dumps(records,indent=2)+'\n')
  audio_raw=c.string_at(dll.gaw_audio_irq_events(),dll.gaw_audio_irq_count()*112);(base/(region+'-audio.bin')).write_bytes(audio_raw)
  audio_events=[struct.unpack_from('<14Q',audio_raw,n) for n in range(0,len(audio_raw),112)]
  for number,(room,seed) in enumerate(ROWS):
   first,last=observed[number];graphics=2 if room>>8 else 1 if room<16 or room&15==15 else 0;asset=(15-graphics)*0x4000+16;expected,used=decode(rom[asset:]);stream=(c.c_uint8*used).from_buffer_copy(rom[asset:asset+used])
   ram=(c.c_uint8*336)(*first['ram']);audio=(c.c_uint8*400)(*first['audio']);out=(c.c_uint32*19)();events=(c.c_uint32*384)();pixels=(c.c_uint8*16384)()
   assert fn((c.c_uint32*12)(*first['phase']),first['refresh'],ram,audio,low,bank,stream,0,room,out,events,pixels),(region,room,seed,'rejected')
   assert bytes(pixels)==expected and out[15]==used,(region,room,seed,'patterns/end')
   assert bytes(audio)==bytes(last['audio']) and all(ram[i]==last['ram'][i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(region,room,seed,'state')
   p=last['phase'];raster=(p[1]*3420+((p[0]-p[2]+0x80000000)&0xffffffff)-0x80000000)%(p[3]*3420)
   assert out[0]==raster and out[2]==last['time']-first['time'],(region,room,seed,'phase',list(out),last['time']-first['time'])
   assert out[10]==last['refresh'] and out[4]+out[6]==last['m1']-first['m1'],(region,room,seed,'M1/R')
   entries=[e[1]-first['time'] for e in audio_events if e[0]==0x137 and first['time']<e[1]<last['time']]
   assert entries==[events[n*6] for n in range(out[7])],(region,room,seed,'IRQ entries')
   assert out[11]==p[8] and out[13]==p[10] and out[14]==1 and not out[12] and not out[16]
   # Compare every byte actually written by the original four-plane routine.
   position=0
   for plane in range(4):
    dest=plane
    while rom[asset+position]:
     command=rom[asset+position];position+=1;count=command&127 or 256
     for k in range(count):assert vram[number][dest]==expected[dest],(region,room,seed,'source VRAM',dest);dest+=4
     position+=count if command&128 else 1
    position+=1
   cases.append(dict(room=room,graphics=graphics,phase=first['phase'],refresh=first['refresh'],ram=first['ram'],audio=first['audio'],expected=list(out),after_ram=list(ram),after_audio=list(audio),events=list(events[:out[7]*6])))
   summaries.append(dict(region=region,room=room,graphics=graphics,seed=seed,foreground_T=out[3],foreground_M1=out[4],irq_count=out[7],wall_master=out[2],entry_R=first['refresh'],exit_R=out[10],packed=used))
  print(region,len(ROWS),'three-class prefix source phase/R/M1/state/VRAM exact',flush=True)
 (base/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
 live=[]
 def path(room):return 'dungeon' if room>>8 else 'house_low' if room<16 else 'house_f' if room&15==15 else 'exterior'
 for region in ['auto','pal']:
  for name in ['house','dungeon']:
   source_path=ROOT/f'validation/standard-door-music/{name}-{region}/source-events.json';events=json.loads(source_path.read_text())
   starts=[e for e in events if e[1]==0x16d0]
   for first in starts:
    last=next(e for e in events if e[1]==0x1706 and e[2]>first[2]);actual=((last[2]-first[2])-(last[3]-first[3]))//15
    expected=next(r['foreground_T'] for r in summaries if r['region']==region and path(r['room'])==path(first[4]))
    assert actual==expected,(name,region,first[4],actual,expected)
    live.append(dict(region=region,route=name,room=first[4],foreground_T=actual,records_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest()))
 print(len(live),'controlled real-door source foreground costs agree',flush=True)
 report=dict(cases=len(cases),rows=summaries,live_door_costs=live,module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_pattern_clock.c').read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(rom).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),limits=['Original16D0..1706,175F and032A execute unchanged;1706 patchedRET is only the exit marker. Custom boot supplies seven rooms,four R seeds,changed bank,display off,timer2 and IM1;acknowledges the initial VDP status before entry;VINT enabled.','Native phase/R,totalM1,331RAM,400audio,IRQ entry times and all decoded bytes checked.Original VRAM is compared over written positions only. Audio begins quiet and evolves dynamically; foreground palette copy intoDCA0 not exposed by this prefix API.','No new production wiring,other175F callers,same-bank early return,display-on fade or remainder of house/dungeon loading is claimed.'])
 (ROOT/'analysis/graphics_classes_prefix_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
