"""Native0938 SAT production compared with the original Z80 routine in GPG."""
import ctypes as c,hashlib,json,os,random,subprocess
from pathlib import Path
from run_core import run
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
class Output(c.Structure):
 _fields_=[('count',c.c_uint16),('y_end',c.c_uint16),('xy_end',c.c_uint16),('rotating',c.c_uint8),('bank',c.c_uint8)]
def scene_seed():
 b=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes());b[0x1d40:0x1e00]=bytes([165])*192;b[0x1100:0x1180]=bytes([90])*128;b[0x303]&=254
 for slot in range(32):b[0x300+slot*48+0x1b:0x300+slot*48+0x1d]=bytes([60,60])
 return bytes(b)
def scene_sat(seed,bank):
 # Independent descriptor reference; native output is not used as expected.
 from sprite_reference import entity_sprites
 rom=bytes(0x30000)+bank;entities=[bytearray(seed[0x300+n*48:0x330+n*48]) for n in range(32)];entities[0][3]|=1
 if seed[0x47]>=8 or seed[0x1b]&64:
  start=(seed[0x2f]&3)*32;order=[(int.from_bytes(bank[start+n*2:start+n*2+2],'little')-0xc300)//48 for n in range(32)];order=[n for n in order if entities[n][0] and entities[n][3]&1]
 else:order=sorted([n for n in range(32) if entities[n][3]&1],key=lambda n:(-entities[n][0x11],n))
 values=[]
 for n in order:values.extend(entity_sprites(rom,entities[n])[0])
 assert len(values)<=64;sat=bytearray(seed[0x1d40:0x1e00])
 for n,(x,y,tile) in enumerate(values):sat[n]=y;sat[64+n*2]=x;sat[65+n*2]=tile
 sat[len(values)]=208;return bytes(sat)
def vectors():
 rom=(ROOT/'input/original.sms').read_bytes();source=ROOT/'validation/sms-vertical-check';capture=json.loads((source/'capture.json').read_bytes());assert capture['rom_sha256']==sha(rom)
 rows=[]
 for f in range(3101,3161):rows.append(('capture-'+str(f),(source/f'ram_{f:05d}.bin').read_bytes()))
 initial=bytearray(rows[19][1]);rng=random.Random(0x9380a60)
 for count in [0,1,6,7,8,12,31,32]:
  for phase in range(4):
   for overflow in [0,64]:
    b=bytearray(initial);b[0x47]=count;b[0x2f]=phase;b[0x1b]=overflow
    # Keep valid ROM actor descriptors while exercising ties, hidden/type0
    # actors, zero-visible hero and the distinct sort/rotating predicates.
    b[0x303]&=254
    for n in range(1,32):
     e=0x300+n*48;b[e]=0;b[e+3]=0
    template=initial[0x600:0x630]
    for n in range(1,5):
     e=0x300+n*48;b[e:e+48]=template;b[e]=0 if n==2 else template[0]
     b[e+3]=0 if n==4 else 1;b[e+0x11]=80 if n<3 else 255;b[e+0x13]=rng.randrange(256)
    b[0x1d40:0x1e00]=rng.randbytes(192);b[0x1100:0x1180]=rng.randbytes(128)
    rows.append((f'matrix-{count}-{phase}-{overflow}',bytes(b)))
 for rotating in [False,True]:
  for phase in range(4):
   b=bytearray(initial);b[0x47]=16 if rotating else 0;b[0x1b]=0;b[0x2f]=phase
   for n in range(32):
    e=0x300+n*48;b[e:e+48]=initial[0x300:0x330];b[e+3]=1 if n<16 else 0;b[e+0x11]=80;b[e+0x13]=(n*17)&255
   rows.append((f'capacity64-{rotating}-{phase}',bytes(b)))
 rows.append(('actor-stream-poisoned',scene_seed()))
 return rom,rows
def fixture(rom,rows):
 # Only the boot/vector and unused caller/data area are changed.0938..0AA3
 # and descriptor/order bank12 remain byte-identical to the supplied ROM.
 image=bytearray(2*1024*1024);image[:len(rom)]=rom
 image[:3]=bytes.fromhex('c30010');image[0x38:0x42]=bytes.fromhex('f5dbbff1fbed4d000000')
 code=bytearray(bytes.fromhex('f331f0dfed56af32fcff32fdff3e0132feff'))
 # Mode4, VINT enabled with display off; custom IRQ just acknowledges VDP.
 code+=bytes.fromhex('3e04d3bf3e80d3bf3ea0d3bf3e81d3bf')
 code+=bytes.fromhex('21ffff2200c0')
 for index,(_,raw) in enumerate(rows):
  assert len(raw)==8192
  bank=16+index//2;address=0x4000+(index%2)*8192;offset=bank*16384+(index%2)*8192;image[offset:offset+8192]=raw
  code+=b'\xf3\x3e'+bytes([bank])+bytes.fromhex('32feff')
  code+=b'\x21'+address.to_bytes(2,'little')+bytes.fromhex('1100c001001fedb0cd3809')
  code+=b'\x21'+index.to_bytes(2,'little')+bytes.fromhex('2200c00603')
  loop=0x1000+len(code);code+=bytes.fromhex('dbbfe680ca')+loop.to_bytes(2,'little')+bytes.fromhex('05c2')+loop.to_bytes(2,'little')
 code+=bytes.fromhex('f376c3')+(0x1000+len(code)+1).to_bytes(2,'little')
 assert len(code)<0x3000;image[0x1000:0x1000+len(code)]=code
 assert image[0x938:0xaa4]==rom[0x938:0xaa4] and image[0x30000:0x34000]==rom[0x30000:0x34000]
 return bytes(image)
def main():
 folder=ROOT/'validation/source-sprite-scene';folder.mkdir(parents=True,exist_ok=True);rom,rows=vectors();sdk=ROOT.parents[1]/'work/sgdk'
 args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(ROOT/'megadrive/src/source_sprite_scene.c'),'-o',str(folder/'scene.dll')]
 env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
 dll=c.CDLL(str(folder/'scene.dll'));fn=dll.source_sprite_scene;p8=c.POINTER(c.c_uint8);fn.argtypes=[p8,p8,c.POINTER(Output)];fn.restype=c.c_uint8
 bank=(c.c_uint8*16384).from_buffer_copy(rom[0x30000:0x34000]);expected=[];stats=[]
 for name,raw in rows:
  ram=(c.c_uint8*8192).from_buffer_copy(raw);out=Output();assert fn(ram,bank,c.byref(out)),name
  expected.append(bytes(ram));stats.append(dict(name=name,count=out.count,rotating=out.rotating,y_end=out.y_end,xy_end=out.xy_end,ram_sha256=sha(bytes(ram))))
 image=fixture(rom,rows);path=folder/'source-fixture.sms';path.write_bytes(image);(folder/'inputs.json').write_text(json.dumps([dict(name=n,ram=list(b)) for n,b in rows]))
 regions=[]
 for region in ['ntsc','pal']:
  seen={};captured=bytearray()
  def observe(frame,ram):
   index=int.from_bytes(ram[:2],'little')
   if index>=len(rows) or index in seen:return
   assert bytes(ram[2:0x1f00])==expected[index][2:0x1f00],(region,index,rows[index][0],[(hex(n),ram[n],expected[index][n]) for n in range(2,0x1f00) if ram[n]!=expected[index][n]][:12])
   seen[index]=frame;captured.extend(index.to_bytes(2,'little')+bytes(ram[:0x1f00]))
  run(path,len(rows)*8+25,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert len(seen)==len(rows),(region,len(seen),len(rows));(folder/(region+'-records.bin')).write_bytes(captured);regions.append(dict(region=region,cases=len(seen),records_sha256=sha(captured)));print(region,len(seen),'original0938 RAM comparisons exact',flush=True)
 invalid=0
 for bad in ['null-ram','null-bank','null-output','bad-table','zero-count','bad-order','capacity']:
  raw=bytearray(rows[19][1]);bb=bytearray(rom[0x30000:0x34000]);raw[0x47]=8
  if bad=='bad-table':raw[0x308:0x30a]=b'\x00\x70'
  if bad in ['zero-count','capacity']:
   # First rotating entry is hero in phase0. Point its table/direction at
   # a deliberate isolated descriptor, without changing production ROM.
   raw[0x2f]=0;raw[0x308:0x30c]=bytes.fromhex('00b00000')
   bb[0x3000:0x3004]=bytes.fromhex('10b020b0');bb[0x3010:0x3012]=bytes.fromhex('20b0');bb[0x3020]=0 if bad=='zero-count' else 65
  if bad=='bad-order':bb[:2]=bytes.fromhex('01c3');raw[0x2f]=0
  ram=(c.c_uint8*8192).from_buffer_copy(raw);b=(c.c_uint8*16384).from_buffer_copy(bb);out=Output();c.memset(c.byref(out),165,c.sizeof(out));before=bytes(ram);oo=bytes(out)
  assert not fn(None if bad=='null-ram' else ram,None if bad=='null-bank' else b,None if bad=='null-output' else c.byref(out)),bad
  assert bytes(ram)==before and bytes(out)==oo,bad;invalid+=1
 report=dict(source_rom_sha256=sha(rom),fixture_sha256=sha(image),sources={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_sprite_scene.c','source_sprite_scene.h']},results=regions,cases=stats,invalid_atomic_checks=invalid,limits=['Original0938..0AA3 plus bank12 unchanged. Custom boot/caller/IRQ and captured or controlled actor inputs.7934 RAM bytes compared per case, excluding only case marker and caller stack page. Source instruction cycle/IRQ interleaving, mapper timing, actor evolution, rendering/full game remain unproved. Native builder rejects invalid descriptors or more than64 accumulated entries atomically.'])
 (ROOT/'analysis/source_sprite_scene_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
