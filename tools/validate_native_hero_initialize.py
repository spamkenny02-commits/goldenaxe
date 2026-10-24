"""Execute native2C63 against original hero fixture, including R/M1 and475 RAM bytes."""
import ctypes as c,json,os,struct,subprocess
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_native_room_finish import MODULES as FINISH_MODULES
from validate_hero_initialization_cost import ROWS,generate
MODULES=['source_hero_initialize',*FINISH_MODULES]
WRAPPER=r'''#include "source_hero_initialize.h"
u8 hero_case(const u32 *phase,u8 refresh,const u8 *rom,u8 *body,u32 *out,u8 *after)
{
 SourceClock k;SourceIrqContext ctx={0};u8 ram[336],audio[400];u16 n;
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;
 while(raster<0){raster+=period;}while((u32)raster>=period){raster-=period;}
 for(n=0;n<80;n++)ram[n]=body[n];
 for(n=0;n<256;n++)ram[80+n]=body[0x1d00+n];
 for(n=0;n<400;n++)audio[n]=body[0x1e00+n];
 ctx.ram=ram;ctx.audio=audio;ctx.full_ram=body;ctx.low=rom;ctx.low_bytes=32768;ctx.bank6=rom+0x18000;ctx.input.lines=phase[3];ctx.input.reset_mask=16;
 if(!source_clock_init(&k,phase[3],raster,refresh,phase[8],phase[9],phase[10]))return 0;
 if(!source_hero_initialize(&k,&ctx,rom,0,0))return 0;
 out[0]=k.elapsed;out[1]=k.foreground_tstates;out[2]=k.foreground_m1;out[3]=k.irq_tstates;out[4]=k.irq_m1;out[5]=k.irq_count;out[6]=k.raster;out[7]=k.refresh;out[8]=k.first;
 for(n=0;n<8192;n++)after[n]=source_room_get(&ctx,n);
 return 1;
}
'''
def main():
 folder=ROOT/'validation/native-hero-initialize';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_bytes(WRAPPER.encode());sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O3','-shared','-Wall','-Wextra','-Werror','-I'+str(sdk/'inc'),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/(n+'.c')) for n in MODULES],str(folder/'wrapper.c'),'-o',str(folder/'hero.dll')],env=env,capture_output=True,text=True)
 (folder/'compile.log').write_bytes((built.stdout+built.stderr).encode());assert built.returncode==0,built.stderr[-3000:]
 original=(ROOT/'input/original.sms').read_bytes();fixture,_=generate();image=fixture.read_bytes();assert image[0x2c63:0x2d9e]==original[0x2c63:0x2d9e] and image[0x369f:0x371d]==original[0x369f:0x371d]
 lib=c.CDLL(str(folder/'hero.dll'));u8=c.POINTER(c.c_uint8);lib.hero_case.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,u8,u8,c.POINTER(c.c_uint32),u8];lib.hero_case.restype=c.c_uint8;rom=(c.c_uint8*len(original)).from_buffer_copy(original)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_herorefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_foreground_phase_samples.restype=c.c_uint
 for n in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_hero_entry','gaw_hero_return']:getattr(engine,n).restype=u8
 results=[];indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0))
 for region in ['auto','pal']:
  engine.gaw_timing_reset();previous=[0];entry=[None];checked=set();done=[];digest=bytearray()
  def observe(f,r):
   if r[4]:done.append(f)
   count=engine.gaw_foreground_phase_samples()
   for i in range(previous[0],count):
    raw=c.string_at(c.cast(engine.gaw_foreground_phase_events(),c.c_void_p).value+i*800,800);meta=c.string_at(c.cast(engine.gaw_foreground_m1_events(),c.c_void_p).value+i*16,16);pc,t=struct.unpack_from('<2Q',raw);m1,refresh,_=struct.unpack('<Q2I',meta)
    if pc==0x2c63:entry[0]=(raw,m1,refresh)
    elif pc==0x24e7:
     first,m0,r0=entry[0];phase=struct.unpack_from('<12I',first,16);start=struct.unpack_from('<Q',first,8)[0];before=c.string_at(engine.gaw_hero_entry(),8192);expected=c.string_at(engine.gaw_hero_return(),8192);case=int.from_bytes(before[:2],'little');body=(c.c_uint8*8192).from_buffer_copy(before);out=(c.c_uint32*9)();after=(c.c_uint8*8192)()
     assert lib.hero_case((c.c_uint32*12)(*phase),r0,rom,body,out,after),(region,case,ROWS[case],'rejected')
     assert out[0]==t-start==out[1]*15 and out[2]==m1-m0 and out[7]==refresh and out[8]==1 and not out[5],(region,case,ROWS[case],'time/M1/R',out[:],t-start,m1-m0,refresh)
     differences=[j for j in indices if after[j]!=expected[j]];assert not differences,(region,case,ROWS[case],'RAM',[(hex(j),after[j],expected[j]) for j in differences[:10]])
     checked.add(case);digest.extend(bytes(out));digest.extend(bytes(after[j] for j in indices))
   previous[0]=count
   if count>24000 and r[2]:engine.gaw_timing_reset();previous[0]=0
  run(fixture,len(ROWS)*5+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==len(ROWS),(region,len(checked),len(ROWS));results.append(dict(region=region,cases=len(checked),output_sha256=sha(digest)));print(results[-1],flush=True)
 report=dict(passed=True,cases=sum(r['cases'] for r in results),rows=results,source_sha256=sha(original),fixture_sha256=sha(image),module_sha256={n+'.c':sha((ROOT/'megadrive/src'/(n+'.c')).read_bytes()) for n in MODULES},headers_sha256={n:sha((ROOT/'megadrive/src'/n).read_bytes()) for n in ['source_hero_initialize.h','source_room_memory.h','source_irq_context.h']},production_clock_wired=False,limits=['Original2C63 and callees unchanged, existing independent-dimension fixture: classes0..2, terrains0..5, selections0..16, directions, gear/curse/tiles/coordinate boundaries. Source IRQs disabled.','Entire475 affected/preserved RAM bytes and actual Z80 time/M1/R match. Not a complete Cartesian product, native68000, interrupted initialization, full loader composition or gameplay proof.'])
 (ROOT/'analysis/native_hero_initialize_report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report)

if __name__=='__main__':main()
