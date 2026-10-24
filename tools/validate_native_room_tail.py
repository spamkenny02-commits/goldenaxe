"""Original5B20/1CAF: class0/1/2 selection, boss/empty flags and music suppression."""
import ctypes as c,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_native_hero_initialize import WRAPPER as HERO_WRAPPER
from validate_native_room_ready import MODULES
WRAPPER=HERO_WRAPPER.replace('source_hero_initialize.h','source_room_ready.h').replace('hero_case(','tail_case(').replace('source_hero_initialize(&k,&ctx,rom,0,0)','source_room_tail(&k,&ctx,rom,0,0)')
def main():
 folder=ROOT/'validation/native-room-tail';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];sdk=ROOT.parents[1]/'work/sgdk'
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'tail.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();rom=fixture(original,False);rom[0x16d7:0x16da]=bytes.fromhex('c3e724');assert rom[0x24e7:0x24f3]==original[0x24e7:0x24f3] and rom[0x1caf:0x1d0d]==original[0x1caf:0x1d0d] and rom[0x5b20:0x5b5a]==original[0x5b20:0x5b5a]
 cart=folder/'fixture.sms';cart.write_bytes(rom);lib=c.CDLL(str(folder/'tail.dll'));u8=c.POINTER(c.c_uint8);lib.tail_case.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,u8,u8,c.POINTER(c.c_uint32),u8];lib.tail_case.restype=c.c_uint8;source_rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_loadertailrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_loader_entry_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_loader_entry_events']:getattr(engine,n).restype=u8
 cases=list(itertools.product([(0,0x95),(0,0x96),(1,0x9f),(1,0xbf),(2,0x151),(2,0x144)],[0,64],[1,128],range(3),[0,3]));results=[];fields=[0x1d,0x62,0x63,0x64,0x65,0xa4,0xa5,0xa8,0xae,0x1e06]+list(range(0x1ce0,0x1ce6))
 for region in ['auto','pal']:
  engine.gaw_timing_reset();pending=[];checked=[0];digest=bytearray()
  def prepare(i,f):
   (graphics,room),boss,count,previous,heading=cases[i];command=(0x84 if (room&255) in original[0x1d02:0x1d0d] else 0x82) if graphics==0 else (0x8b if room==0xbf else 0x87) if graphics==1 else (0x86 if boss else 0x83);previous=[command,0,0xb0][previous];actors=bytearray(768);actors[3]=boss
   pending[:]=[(f,0x40,bytes([graphics])),(f,0xb9,room.to_bytes(2,'little')),(f,0x600,bytes(actors)),(f,0x60,bytes.fromhex('3412a5a5a5')+bytes([previous])),(f,0x30a,bytes([heading])),(f,0xa2,bytes([count])),(f,0xa8,b'\x5a'),(f,0xae,b'\xa7'),(f,0x1ce0,bytes([0xa7])*6),(f,0x1e06,b'\x9a'),(f,0x80,bytes([i&255,0,0,0])),(f,0x1d00,b'\1')]
  def observe(f,r):
   if f<11 or (f-11)%2:return
   i=(f-11)//2
   if i>=len(cases):return
   assert not r[0x1d00];count=engine.gaw_foreground_phase_samples();raw=c.string_at(engine.gaw_foreground_phase_events(),count*800);meta=c.string_at(engine.gaw_foreground_m1_events(),count*16);positions=[n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0] in [0x24e7,0x1706]];assert len(positions)==2;a,b=positions
   phase=struct.unpack_from('<12I',raw,a*800+16);ta=struct.unpack_from('<Q',raw,a*800+8)[0];tb=struct.unpack_from('<Q',raw,b*800+8)[0];fa,refresh,_=struct.unpack_from('<Q2I',meta,a*16);fb,end_r,_=struct.unpack_from('<Q2I',meta,b*16)
   assert engine.gaw_loader_entry_samples()==1;initial=c.string_at(engine.gaw_loader_entry_events(),8200)[8:];body=(c.c_uint8*8192).from_buffer_copy(initial);out=(c.c_uint32*9)();after=(c.c_uint8*8192)();assert lib.tail_case((c.c_uint32*12)(*phase),refresh,source_rom,body,out,after)
   assert out[0]==tb-ta==out[1]*15 and out[2]==fb-fa and out[7]==end_r and out[8]==1 and not out[5],(region,i,cases[i],'time/M1/R',out[:],tb-ta,fb-fa,end_r)
   assert all(after[j]==r[j] for j in fields),(region,i,cases[i],'RAM/music',[(hex(j),after[j],r[j]) for j in fields if after[j]!=r[j]])
   digest.extend(bytes(out));digest.extend(bytes(after[j] for j in fields));checked[0]+=1;engine.gaw_timing_reset()
   if i+1<len(cases):prepare(i+1,f+1)
  prepare(0,10);run(cart,len(cases)*2+9,folder/region,set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region});assert checked[0]==len(cases);results.append(dict(region=region,cases=checked[0],output_sha256=sha(digest)));print(results[-1],flush=True)
 report=dict(passed=True,cases=sum(r['cases'] for r in results),rows=results,source_sha256=sha(original),fixture_sha256=sha(rom),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},production_clock_wired=False,limits=['Original24E7 return/scripts/music routines unchanged, test caller jumps directly to24E7 and returns through a10T JP to1706 instead of1FA7. Both prefetched boundaries have identical M1/time semantics.','Classes0..2, normal/special exterior and house music, boss bit, empty count, previous-command suppression and headings; source IRQs disabled. Native68000/live IRQ/full-chain proof remains the separate ordinary class0 matrix.'])
 (ROOT/'analysis/native_room_tail_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)

if __name__=='__main__':main()
