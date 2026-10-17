"""Batched0C00 against immutable scalar C, including IRQ boundaries and bytes."""
import ctypes as c
import hashlib
import json
import os
import random
import subprocess
from actor_reference import ROOT
from validate_native_graphics_load import MODULES

WRAPPER='''#include "source_ram_planes.h"
u8 source_ram_planes_scalar(SourceClock*,SourceIrqContext*,const u8**,u8*,u16,u8);
typedef struct {u32 count,data[64][5];} Log;
static void trace(void *user,const SourceClockIrq *entry,const SourceClockWork *work)
{
 Log *p=(Log*)user;u32 *r;if(p->count>=64) {p->count++;return;}
 r=p->data[p->count++];r[0]=entry->entry_elapsed;r[1]=entry->entry_raster;r[2]=entry->entry_refresh;r[3]=work->tstates;r[4]=work->fetches;
}
u8 ram_case(u8 scalar,u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,u16 address,u8 stride,
              const u8 *low,const u8 *bank,const u8 *stream,u8 *pixels,u32 *out,u32 *events,u8 *state)
{
 SourceClock clock;SourceIrqContext ctx={0};u8 ram[336]={0},audio[400]={0};Log log={0};const u8 *end=stream;u16 n,j;
 audio[3]=lines==262?0x80:0;
 if(!source_clock_init(&clock,lines,raster,refresh,iff,0,pending)) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.bank6=bank;ctx.input.lines=lines;ctx.input.reset_mask=16;ctx.trace=trace;ctx.trace_context=&log;
 for(n=0;n<16384;n++) pixels[n]=0xa7;
 if(!(scalar?source_ram_planes_scalar(&clock,&ctx,&end,pixels,address,stride):source_ram_planes(&clock,&ctx,&end,pixels,address,stride)) || log.count>64) return 0;
 if(!source_clock_checkpoint(&clock,source_irq_interrupt,&ctx)) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;
 out[5]=clock.irq_tstates;out[6]=clock.irq_m1;out[7]=clock.irq_count;out[8]=clock.refresh;out[9]=clock.iff;out[10]=clock.blocked;out[11]=clock.pending;out[12]=clock.first;
 out[13]=clock.status_suppressions;out[14]=clock.vector_coalescences;out[15]=end-stream;out[16]=ctx.audio_de;out[17]=ctx.error;
 for(n=0;n<log.count;n++) for(j=0;j<5;j++) events[n*5+j]=log.data[n][j];
 for(n=0;n<336;n++) state[n]=ram[n];
 for(n=0;n<400;n++) state[336+n]=audio[n];
 return 1;
}
'''

def streams(stride):
    yield bytes(stride)
    yield b''.join(bytes([128])+bytes(range(256))+bytes([0]) for n in range(stride))
    rng=random.Random(0xc00+stride)
    for case in range(128):
        data=bytearray()
        for plane in range(stride):
            for run in range(rng.randrange(1,7)):
                literal=rng.randrange(2);count=256 if literal and case%17==0 else rng.randrange(1,128)
                data.append((128 if literal else 0)|(count&127));data.extend(rng.randbytes(count if literal else 1))
            data.append(0)
        yield bytes(data)

def main():
    folder=ROOT/'validation/ram-clock-batch';folder.mkdir(exist_ok=True)
    reference=ROOT/'analysis/native-room-finish-v0198/megadrive/src/source_ram_planes.c'
    (folder/'reference.c').write_text(reference.read_text().replace('source_ram_planes(','source_ram_planes_scalar('));(folder/'wrapper.c').write_text(WRAPPER)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'reference.c'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES);args.extend(['-o',str(folder/'ram.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'ram.dll'));fn=dll.ram_case
    fn.argtypes=[c.c_uint8,c.c_uint16,c.c_uint32,*([c.c_uint8]*3),c.c_uint16,c.c_uint8,*([c.POINTER(c.c_uint8)]*4),c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint8)];fn.restype=c.c_uint8
    rom=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(rom[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(rom[0x18000:0x1c000]);cases=0;digest=hashlib.sha256()
    for stride in [1,2,4]:
        for number,stream in enumerate(streams(stride)):
            for lines in [262,313]:
                for iff,pending in [(1,0),(1,1),(0,1)]:
                    raster=(193*3420-(number%31+1))%(lines*3420);address=[0xc900,0xc9fd,0xd100,0xdb00,0xdcff,0xfffd][number%6]
                    packed=(c.c_uint8*len(stream)).from_buffer_copy(stream);results=[]
                    for scalar in [0,1]:
                        pixels=(c.c_uint8*16384)();output=(c.c_uint32*18)();events=(c.c_uint32*320)();state=(c.c_uint8*736)()
                        assert fn(scalar,lines,raster,number&255,iff,pending,address,stride,low,bank,packed,pixels,output,events,state),('rejected',cases,scalar)
                        results.append((list(output),list(events[:output[7]*5]),bytes(state),bytes(pixels)))
                    assert results[0]==results[1],(cases,stride,address,lines,iff,pending)
                    digest.update(results[0][-1]);cases+=1
    report=dict(cases=cases,reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_ram_planes.c').read_bytes()).hexdigest(),output_digest=digest.hexdigest(),
                limits=['Host pairwise all16384 bytes,336RAM/400audio,clock/IRQ logs against immutable scalar C. Generated1/2/4-plane streams,count256,page/end carry,VINT/refresh/IFF/pending variations.',
                        'Logical address carry tests include synthetic wrap; original-game source/68000 chain comparisons are separate.'])
    (ROOT/'analysis/ram_clock_batch_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
