"""All512 room lists, six persistence masks and three boss progress states on Z80/C."""
import ctypes as c,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_history_timed import fixture
from validate_reveal_phase_prediction import raster as source_raster

WRAPPER=r'''
#include "source_actor_list.h"
#include "source_rng_timed.h"
u8 source_irq_interrupt(void *ctx,const SourceClockIrq *entry,SourceClockWork *work){return 0;}
u8 actor_case(u16 lines,u32 raster,u8 refresh,u16 room,u8 mask,u8 progress,const u8 *bank12,u32 *out,u8 *actors)
{
 SourceClock k;SourceIrqContext ctx={0};u8 ram[336]={0},rb[2],masks[256],progression[256],count,sample;u16 i;
 SourceActorListData data={actors,&count,rb,masks,progression};
 for(i=0;i<256;i++){masks[i]=mask;progression[i]=progress;}
 rb[0]=room;rb[1]=room>>8;ram[0x37]=5;ctx.ram=ram;
 if(!source_clock_init(&k,lines,raster,0,0,0,0))return 0;
 if(!source_clock_plain(&k,4,1,0,0) || !source_clock_plain(&k,13,1,0,0) || !source_clock_plain(&k,9,2,0,0))return 0;
 k.refresh=refresh;
 if(!source_clock_plain(&k,4,1,0,0) || !source_clock_plain(&k,10,1,0,0) || !source_clock_checkpoint(&k,0,0))return 0;
 if(!source_actor_list(&k,&ctx,bank12,&data,0,0) || !source_clock_plain(&k,10,1,0,0) || !source_clock_checkpoint(&k,0,0))return 0;
 out[0]=k.elapsed;out[1]=k.foreground_tstates;out[2]=k.foreground_m1;out[3]=k.raster;out[5]=count;
 if(!source_rng_read_refresh(&k,&sample,0,0))return 0;
 out[4]=sample;return 1;
}
'''

def main():
 folder=ROOT/'validation/native-actor-list';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 modules=['source_actor_list','source_clock','source_rng','source_rng_timed']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-shared','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in modules],str(folder/'wrapper.c'),'-o',str(folder/'actor.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr
 host=c.CDLL(str(folder/'actor.dll'));u8=c.POINTER(c.c_uint8);host.actor_case.argtypes=[c.c_uint16,c.c_uint32,c.c_uint8,c.c_uint16,c.c_uint8,c.c_uint8,u8,c.POINTER(c.c_uint32),u8];host.actor_case.restype=c.c_uint8
 original=(ROOT/'input/original.sms').read_bytes();rom=fixture(original,False);rom[0x16d7:0x16da]=bytes.fromhex('c38017');rom[0x1853:0x1856]=bytes.fromhex('c30617');assert rom[0x1780:0x1853]==original[0x1780:0x1853] and rom[0x30000:0x34000]==original[0x30000:0x34000]
 cart=folder/'fixture.sms';cart.write_bytes(rom);bank=(c.c_uint8*16384).from_buffer_copy(original[0x30000:0x34000]);core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_actorprefixrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events']:getattr(engine,n).restype=c.POINTER(c.c_uint8)
 cases=list(itertools.product(range(512),[0,1,0x55,0xaa,0xfe,255],[0,1,128]));pending=[];checked=[0];boss=[0];gem=[0];removed=[0];digest=bytearray()
 def prepare(i,f):
  room,mask,progress=cases[i];refresh=[0,127,128,255][i%4];pending[:]=[(f,0xb9,room.to_bytes(2,'little')),(f,0x200,bytes([mask])*256),(f,0xce,bytes([progress])*256),(f,0x37,b'\5'),(f,0x80,bytes([refresh,0,0,0])),(f,0x600,bytes([0xa7])*768),(f,0x1d00,b'\1')]
 def observe(f,ram):
  if f<11 or (f-11)%2:return
  i=(f-11)//2
  if i>=len(cases):return
  assert not ram[0x1d00],('unfinished',i)
  count=engine.gaw_foreground_phase_samples();ptr=engine.gaw_foreground_phase_events();raw=c.string_at(ptr,count*800);positions=[n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0] in [0x16d0,0x1706]];assert len(positions)==2
  a,b=positions;phases=[struct.unpack_from('<12I',raw,n*800+16) for n in [a,b]];times=[struct.unpack_from('<Q',raw,n*800+8)[0] for n in [a,b]];m1=c.string_at(engine.gaw_foreground_m1_events(),count*16);fa,_,_=struct.unpack_from('<Q2I',m1,a*16);fb,r1,_=struct.unpack_from('<Q2I',m1,b*16)
  room,mask,progress=cases[i];refresh=[0,127,128,255][i%4];out=(c.c_uint32*6)();actors=(c.c_uint8*768)(*([0xa7]*768));assert host.actor_case(262,source_raster(phases[0]),refresh,room,mask,progress,bank,out,actors)
  assert bytes(actors)==ram[0x600:0x900] and out[5]==ram[0xa2],('actors/count',i,cases[i],[(j,a,b) for j,(a,b) in enumerate(zip(actors,ram[0x600:0x900])) if a!=b][:8])
  assert out[0]==times[1]-times[0]==out[1]*15 and out[2]==fb-fa and out[3]==source_raster(phases[1]),('time/phase/M1',i,cases[i],out[:],times,fb-fa)
  assert out[4]==ram[0x1d04] and ((out[4]&128)|((out[4]-1)&127))==r1,('R',i)
  initial_types=original[0x3234e+room*8:0x32356+room*8];has_boss=any(t>=32 and original[0x320ea+(t-32)*4+3]&64 and mask&(128>>n) for n,t in enumerate(initial_types))
  if has_boss:
   boss[0]+=1
   if progress==1:gem[0]+=1;assert actors[0]==15 and not any(actors[1:384])
   if progress==128:removed[0]+=1;assert not any(actors[:384])
  checked[0]+=1;digest.extend(bytes(actors));digest.extend(bytes(out));engine.gaw_timing_reset()
  if i+1<len(cases):prepare(i+1,f+1)
 engine.gaw_timing_reset();prepare(0,10);run(cart,len(cases)*2+9,folder/'source',set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe)
 assert checked[0]==len(cases) and gem[0] and removed[0]
 report=dict(passed=True,cases=checked[0],rooms=512,masks=6,progress_states=3,boss_cases=boss[0],gem_replacements=gem[0],boss_clears=removed[0],source_sha256=sha(original),fixture_sha256=sha(rom),core_sha256=sha(core.read_bytes()),output_sha256=sha(digest),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in modules},production_clock_wired=False,limits=['Original1780..1852 and bank12 unchanged. Controlled room/masks/progression/entryR, source interrupts disabled. Entire768 actor bytes,count,cycles,M1,R,raster compare.','Live IRQ composition and native68000 execution are separately checked on24 ordinary exterior paths; no interrupted boss-suppression claim.'])
 (ROOT/'analysis/native_actor_list_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)

if __name__=='__main__':main()
