"""Whole room/HUD batching versus immutable scalar C with varied IRQ phases."""
import ctypes as c,hashlib,json,os,subprocess
from actor_reference import ROOT
from validate_native_room_hud import MODULES
from validate_ram_clock_batch import WRAPPER as RAM_WRAPPER

WRAPPER=RAM_WRAPPER[:RAM_WRAPPER.index('u8 ram_case')].replace('#include "source_ram_planes.h"','#include "source_room_hud.h"').replace('u8 source_ram_planes_scalar(SourceClock*,SourceIrqContext*,const u8**,u8*,u16,u8);','u8 source_room_hud_scalar(SourceClock*,SourceIrqContext*,SourceGraphicsData*,SourceWorldMapData*,const u8*,const u8*,SourceGraphicsCheckpoint,void*);')+'''u8 hud_case(u8 scalar,u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,
 const u8 *low,const u8 *bank,const u8 *bank4,const u8 *hud,u8 *memory,u32 *out,u32 *events)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceGraphicsData graphics={0};SourceWorldMapData map={0};
 u8 ram[336]={0},audio[400]={0},tiles[2048];Log log={0};u16 n,j;
 audio[3]=lines==262?0x80:0;
 if(!source_clock_init(&clock,lines,raster,refresh,iff,0,pending)) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.bank6=bank;ctx.input.lines=lines;ctx.input.reset_mask=16;ctx.trace=trace;ctx.trace_context=&log;
 for(n=0;n<2048;n++) tiles[n]=(n*13+(n>>3))&255;
 for(n=0;n<1792;n++) memory[n]=(n*71+refresh)&255;
 graphics.metatiles=tiles;map.tilemap=memory;map.cells=memory+1536;
 if(!(scalar?source_room_hud_scalar(&clock,&ctx,&graphics,&map,bank4,hud,0,0):source_room_hud_prepare(&clock,&ctx,&graphics,&map,bank4,hud,0,0)) || log.count>64) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;
 out[5]=clock.irq_tstates;out[6]=clock.irq_m1;out[7]=clock.irq_count;out[8]=clock.refresh;out[9]=clock.iff;out[10]=clock.blocked;out[11]=clock.pending;out[12]=clock.first;
 out[13]=clock.status_suppressions;out[14]=clock.vector_coalescences;out[15]=ctx.audio_de;out[16]=ctx.error;
 for(n=0;n<log.count;n++) for(j=0;j<5;j++) events[n*5+j]=log.data[n][j];
 for(n=0;n<336;n++) memory[1792+n]=ram[n];
 for(n=0;n<400;n++) memory[2128+n]=audio[n];
 return 1;
}
'''

def main():
 folder=ROOT/'validation/hud-clock-batch';folder.mkdir(exist_ok=True)
 reference=ROOT/'analysis/native-room-finish-v0198/megadrive/src/source_room_hud.c'
 (folder/'reference.c').write_text(reference.read_text().replace('source_room_hud_prepare(','source_room_hud_scalar(').replace('source_hud_prepare(','source_hud_scalar('));(folder/'wrapper.c').write_text(WRAPPER)
 sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'reference.c'),str(folder/'wrapper.c')]
 args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'hud.dll')])
 built=subprocess.run(args,env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
 dll=c.CDLL(str(folder/'hud.dll'));fn=dll.hud_case
 fn.argtypes=[c.c_uint8,c.c_uint16,c.c_uint32,*([c.c_uint8]*3),*([c.POINTER(c.c_uint8)]*5),c.POINTER(c.c_uint32),c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
 rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000]);bank4=(c.c_uint8*16384).from_buffer_copy(rom[0x10000:0x14000]);cases=0;digest=hashlib.sha256()
 for number in range(256):
  cap=[0,7,8,16,24,64,128,129,255][number%9];health=number;magic=(number*73)&255
  hud=(c.c_uint8*16)(health,cap,magic,cap,(number*53)&255,*[128 if (number*29)&(1<<n) else 0 for n in range(9)],0,number&3)
  for lines in [262,313]:
   for mode,(iff,pending) in enumerate([(1,0),(1,1),(0,1)]):
    raster=(193*3420-[1,9900,40000][mode]-(number*97))%(lines*3420);results=[]
    for scalar in [0,1]:
     memory=(c.c_uint8*2528)();output=(c.c_uint32*17)();events=(c.c_uint32*320)()
     assert fn(scalar,lines,raster,number,iff,pending,low,bank,bank4,hud,memory,output,events),('rejected',number,lines,mode,scalar)
     results.append((list(output),list(events[:output[7]*5]),bytes(memory)))
    assert results[0]==results[1],(number,lines,mode,results[0][0],results[1][0])
    digest.update(results[0][-1]);cases+=1
 report=dict(cases=cases,reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),helpers={name:hashlib.sha256((ROOT/'megadrive/src'/name).read_bytes()).hexdigest() for name in ['source_clock.h','source_room_hud.c','source_ram_planes.c']},output_digest=digest.hexdigest(),limits=['Host pairwise1536 tilemap bytes,256 cells,336RAM,400audio,full clock andIRQ entry/work traces. All256 health/magic/gold values independently,selected capacity boundaries and gem masks,not Cartesian product.','Quiet initial audio; varied NTSC/PAL VINT/IFF/pending phases. Full source and compiled68000 chain comparisons remain separate.'])
 (ROOT/'analysis/hud_clock_batch_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
