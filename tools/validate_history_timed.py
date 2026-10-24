"""Execute unchanged1C15 history/RNG on Z80; compare native C phase/R/IRQ/state."""
import argparse,ctypes as c,hashlib,itertools,json,os,struct,subprocess
from run_core import ROOT,run
from validate_reveal_phase_prediction import raster as source_raster
class Data(c.Structure):_fields_=[(n,c.POINTER(c.c_uint8)) for n in ['room','seed','history','masks']]
class Out(c.Structure):_fields_=[(n,c.c_uint8) for n in ['calls','restored','last_value']]
WRAPPER=r'''
#include "source_room_history_timed.h"
u8 run_history(u16 lines,u32 raster,u8 refresh,u8 enabled,u8 *room,u8 *seed,u8 *history,u8 *masks,u32 *out);
static u8 irq(void *c,const SourceClockIrq *e,SourceClockWork *w){w->tstates=563;w->fetches=59;return 1;}
u8 run_history(u16 lines,u32 raster,u8 refresh,u8 enabled,u8 *room,u8 *seed,u8 *history,u8 *masks,u32 *out)
{
 SourceClock k;SourceRoomHistoryData d={room,seed,history,masks};SourceRoomHistoryOutput r;u8 sampled;
 if(!source_clock_init(&k,lines,raster,0,enabled,0,0))return 0;
 if(!source_clock_execute(&k,4,1,SOURCE_CLOCK_DI,irq,0) || !source_clock_plain(&k,13,1,irq,0) || !source_clock_plain(&k,9,2,irq,0))return 0;
 k.refresh=refresh;
 if(!source_clock_execute(&k,4,1,enabled?SOURCE_CLOCK_EI:SOURCE_CLOCK_NONE,irq,0) || !source_clock_plain(&k,10,1,irq,0) || !source_clock_checkpoint(&k,irq,0))return 0;
 if(!source_room_history_timed(&k,&d,&r,irq,0) || !source_clock_plain(&k,10,1,irq,0) || !source_clock_checkpoint(&k,irq,0))return 0;
 out[0]=k.elapsed;out[1]=k.foreground_tstates;out[2]=k.foreground_m1;out[3]=k.irq_tstates;out[4]=k.irq_m1;out[5]=k.irq_count;out[6]=k.raster;out[7]=r.calls;out[8]=r.restored;
 if(!source_rng_read_refresh(&k,&sampled,irq,0))return 0;
 out[9]=sampled;return 1;
}
'''

def compile(folder,prefix=False):
 wrapper=WRAPPER
 if prefix:
  wrapper=wrapper.replace("SourceClock k;", "u8 flags[32],objects[336];memset(flags,0xa7,32);memset(objects,0xcc,336);SourceClock k;")
  wrapper='#include <string.h>\n'+wrapper.replace("source_room_history_timed(&k,&d,&r,irq,0)","source_room_actor_prefix(&k,flags,objects,&d,&r,irq,0)")
  wrapper=wrapper.replace("out[0]=k.elapsed", "for(u16 i=0;i<32;i++){if(flags[i])return 0;}\n for(u16 i=0;i<336;i++){if(objects[i])return 0;}\n out[0]=k.elapsed")
 (folder/'types.h').write_text('#include <stdint.h>\ntypedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;\n');(folder/'wrapper.c').write_text(wrapper);env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 names=['source_clock.c','source_rng.c','source_rng_timed.c','source_room_history_timed.c']
 subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-shared','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I'+str(folder),'-I'+str(ROOT/'megadrive/src'),*[str(ROOT/'megadrive/src'/n) for n in names],str(folder/'wrapper.c'),'-o',str(folder/'history.dll')],env=env,check=True)
 lib=c.CDLL(str(folder/'history.dll'));lib.run_history.argtypes=[c.c_uint16,c.c_uint32,c.c_uint8,c.c_uint8]+[c.POINTER(c.c_uint8)]*4+[c.POINTER(c.c_uint32)];lib.run_history.restype=c.c_uint8;return lib

def fixture(original,enabled,prefix=False):
 rom=bytearray(original);base=0x3000;code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=base+len(code)
 def branch(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331e0df2100c01101c001ff1f3600edb0')
 emit('3e04d3bf3e80d3bf3ea0d3bf3e81d3bf3e01320ade')
 if enabled:emit('fb00')
 label('wait');emit('3a00ddb7');branch('ca','wait');emit('2a82c07cb5');branch('ca','ready')
 label('delay');emit('2b7cb5');branch('c2','delay') # DEC HL; LD A,H; OR L; JP NZ =24T.
 label('ready');emit('31e0dfdbbfcdd016c30617')
 for pos,n in fix:code[pos:pos+2]=labels[n].to_bytes(2,'little')
 rom[:3]=bytes.fromhex('c30030');rom[base:base+len(code)]=code
 tramp=bytes.fromhex('f33a80c0ed4f')+bytes([0xfb if enabled else 0])+bytes.fromhex('c3bf24' if prefix else 'c3151c');rom[0x16d0:0x16d0+len(tramp)]=tramp
 post=bytes.fromhex('ed5f3204ddaf3200ddc3')+labels['wait'].to_bytes(2,'little');rom[0x1706:0x1706+len(post)]=post
 if prefix:
  assert rom[0x24bf:0x24e4]==original[0x24bf:0x24e4]
  rom[0x1780:0x1783]=bytes.fromhex('c30617')
 assert rom[0x1c15:0x1c97]==original[0x1c15:0x1c97];return rom

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prefix',action='store_true');a=parser.parse_args();name='history-prefix-timed' if a.prefix else 'history-timed';folder=ROOT/('validation/'+name);folder.mkdir(exist_ok=True);lib=compile(folder,a.prefix);original=(ROOT/'input/original.sms').read_bytes();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_graphicsprefixrefresh_libretro.dll';engine=c.CDLL(str(core));engine.gaw_timing_count.restype=c.c_uint;engine.gaw_timing_events.restype=c.POINTER(c.c_uint64);engine.gaw_foreground_phase_samples.restype=c.c_uint;engine.gaw_foreground_phase_events.restype=c.POINTER(c.c_uint8);engine.gaw_foreground_m1_events.restype=c.POINTER(c.c_uint8)
 cases=[]
 for room,seed,refresh,style,mask,delay in itertools.product([0x95,0x151],[0,1,0x8000,0xffff],[0,127,128,255],range(4),[0,1,255],[0,1790,1820]):
  h=bytearray([0x70]*16);length=4 if room>>8 else 16
  if style==1:h[0]=room&255
  if style==2:h[length-1]=room&255
  if style==3:h[:]=bytes(range(16))
  cases.append((room,seed,refresh,bytes(h),bytes([mask]*256),delay))
 allrows=[];native_cases=[]
 for region,lines in [('auto',262),('pal',313)]:
  for enabled in [0,1]:
   cart=folder/f'fixture-{region}-{enabled}.sms';cart.write_bytes(fixture(original,enabled,a.prefix));engine.gaw_timing_reset();pending=[];checked=[0];irq_cases=[0];total_irq=[0];events=[0];phase_count=[0]
   def prepare(i,f):
    room,seed,r,h,m,delay=cases[i];pending[:]=[(f,0xb9,room.to_bytes(2,'little')),(f,0x28,seed.to_bytes(2,'little')),(f,0x1cf0,h),(f,0x200,m),(f,0x80,bytes([r,0])+delay.to_bytes(2,'little')),(f,0x1d00,b'\1')]+([(f,0x90,bytes([0xa7])*32),(f,0x4b0,bytes([0xcc])*336)] if a.prefix else [])
   def observe(f,ram):
    if f<11 or (f-11)%2:return
    i=(f-11)//2
    if i>=len(cases):return
    if a.prefix:assert ram[0x90:0xb0]==bytes(32) and ram[0x4b0:0x600]==bytes(336),('cleared buffers',region,enabled,i)
    assert ram[0x1d00]==0,('unfinished source',region,enabled,i)
    count=engine.gaw_timing_count();ptr=engine.gaw_timing_events();e=[tuple(ptr[j*8+k] for k in range(8)) for j in range(events[0],count)];events[0]=count
    pair=[r for r in e if r[0] in [0x16d0,0x1706]];assert len(pair)==2 and pair[0][0]==0x16d0 and pair[1][0]==0x1706,(region,enabled,i,pair)
    oldphase=phase_count[0];phase_count[0]=engine.gaw_foreground_phase_samples();assert phase_count[0]-oldphase==2
    rawphase=c.string_at(c.cast(engine.gaw_foreground_phase_events(),c.c_void_p).value+oldphase*800,1600);phases=[struct.unpack_from('<12I',rawphase,k*800+16) for k in range(2)]
    m1=c.string_at(c.cast(engine.gaw_foreground_m1_events(),c.c_void_p).value+oldphase*16,32);fetch0,r0,_=struct.unpack_from('<Q2I',m1,0);fetch1,r1,_=struct.unpack_from('<Q2I',m1,16)
    start,end=pair;room,seed,r,h,m,delay=cases[i];rb=(c.c_uint8*2).from_buffer_copy(room.to_bytes(2,'little'));sb=(c.c_uint8*2).from_buffer_copy(seed.to_bytes(2,'little'));hb=(c.c_uint8*16).from_buffer_copy(h);mb=(c.c_uint8*256).from_buffer_copy(m);out=(c.c_uint32*10)();raster=source_raster(phases[0])
    assert lib.run_history(lines,raster,r,enabled,rb,sb,hb,mb,out)
    assert (bytes(sb),bytes(hb),bytes(mb))==(ram[0x28:0x2a],ram[0x1cf0:0x1d00],ram[0x200:0x300]),('state',region,enabled,i,room,seed,r,out[:],bytes(sb).hex(),ram[0x28:0x2a].hex(),bytes(hb).hex(),ram[0x1cf0:0x1d00].hex(),ram[0x1d04],start,end,[(j,a,b) for j,(a,b) in enumerate(zip(mb,ram[0x200:0x300])) if a!=b][:10])
    assert out[9]==ram[0x1d04],('R',region,enabled,i,out[:],ram[0x1d04])
    wall=end[1]-start[1];irq=end[2]-start[2]
    assert out[0]==wall and out[3]*15==irq and out[1]*15==wall-irq,('cycles',region,enabled,i,out[:],wall,irq,raster)
    assert out[6]==source_raster(phases[1]) and out[7]==(5 if room>>8 else 3)
    assert out[2]+out[4]==fetch1-fetch0,('M1',region,enabled,i,out[:],fetch1-fetch0)
    assert ((out[9]&128)|((out[9]-1)&127))==r1
    irq_cases[0]+=bool(out[5]);total_irq[0]+=out[5];checked[0]+=1
    native_cases.append(dict(input=[lines,raster,r,enabled,room,seed],history=h.hex(),masks=m.hex(),expected=[*out],seed=bytes(sb).hex(),history_after=bytes(hb).hex(),masks_after=bytes(mb).hex()))
    engine.gaw_timing_reset();events[0]=phase_count[0]=0
    if i+1<len(cases):prepare(i+1,f+1)
   prepare(0,10);run(cart,len(cases)*2+9,folder/f'{region}-{enabled}',set(),[],core=core,skip_intro=False,ram_writes=pending,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert checked[0]==len(cases);allrows.append(dict(region=region,enabled=enabled,cases=checked[0],interrupted=irq_cases[0],irqs=total_irq[0]));print(allrows[-1],flush=True)
 assert sum(r['interrupted'] for r in allrows)>0
 (folder/'cases.json').write_text(json.dumps(native_cases,separators=(',',':')))
 report=dict(prefix_to_actor_loader=a.prefix,passed=True,rows=allrows,total_cases=len(native_cases),source_sha256=hashlib.sha256(original).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),module_sha256={n:hashlib.sha256((ROOT/'megadrive/src'/n).read_bytes()).hexdigest() for n in ['source_clock.c','source_rng.c','source_rng_timed.c','source_room_history_timed.c','source_room_history_timed.h']},production_integrated=False,limits=['Unchanged1C15..1C96 and optional24BF..24E3 on original Z80, controlled room/seed/R/history/masks and source entry phase observed from timing core.','Both IRQ-disabled and enabled fixtures, paused563T/59M1 audio IRQ model. Complete seed/history/masks, wall/foreground/IRQ time and sampled R compare.','No whole-game entry clock propagation, live nonpaused audio, native gameplay RNG replacement or campaign claim.'])
 (ROOT/('analysis/'+name.replace('-','_')+'_source_report.json')).write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
