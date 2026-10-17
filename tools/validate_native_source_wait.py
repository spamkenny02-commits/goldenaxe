"""Native wait + clock + dynamic native IRQ/audio against source snapshots."""
import ctypes as c
import hashlib
import json
import os
import struct
import subprocess
from actor_reference import ROOT
from validate_native_audio_reader import MODULES as AUDIO_MODULES

MODULES=['source_wait','source_irq_context','source_irq','source_clock','source_rng',*AUDIO_MODULES]
WRAPPER='''#include "source_wait.h"
typedef struct {u32 count,events[16][6];SourceIrqContext *irq;} WaitTrace;
static void trace(void *context,const SourceClockIrq *entry,const SourceClockWork *work)
{
 WaitTrace *p=(WaitTrace *)context;u32 *row;
 if(p->count>=16) {p->count++;return;}
 row=p->events[p->count++];row[0]=entry->entry_elapsed;row[1]=entry->entry_raster;
 row[2]=entry->entry_refresh;row[3]=work->tstates;row[4]=work->fetches;
 row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
u8 wait_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,
              const u8 *bank6,u16 tile_count,u32 *out,u32 *events)
{
 SourceClock clock;SourceIrqContext ctx={0};SourceWaitOutput result;WaitTrace log={0};
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;u16 n,j;
 if((phase[3]!=262 && phase[3]!=313) || phase[5] || (phase[6]&4) || !(phase[6]&32) ||
    (phase[7]!=32 && phase[7]!=33) || (phase[11]&16)) return 0;
 while(raster<0) raster+=period;
 while((u32)raster>=period) raster-=period;
 if(!source_clock_init(&clock,phase[3],raster,refresh,phase[8],phase[9],phase[10])) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.bank6=bank6;ctx.low_bytes=32768;
 ctx.input.lines=phase[3];ctx.input.tile_count=tile_count;ctx.input.reset_mask=16;
 ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;
 if(!source_wait(&clock,&ctx,&result) || log.count>16) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;
 out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;out[5]=clock.irq_tstates;out[6]=clock.irq_m1;
 out[7]=clock.irq_count;out[8]=clock.status_suppressions;out[9]=clock.vector_coalescences;
 out[10]=clock.refresh;out[11]=clock.iff;out[12]=clock.blocked;out[13]=clock.pending;out[14]=clock.first;
 out[15]=result.taken;out[16]=ctx.error;out[17]=ctx.audio_de;
 for(n=0;n<log.count;n++) for(j=0;j<6;j++) events[n*6+j]=log.events[n][j];
 return 1;
}
'''


def compile_helper():
    folder=ROOT/'validation/native-source-wait';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER)
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared',
          '-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES)
    args.extend(['-o',str(folder/'source_wait.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'source_wait.dll'));function=dll.wait_case
    function.argtypes=[c.POINTER(c.c_uint32),c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),
                       c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.c_uint16,c.POINTER(c.c_uint32),c.POINTER(c.c_uint32)]
    function.restype=c.c_uint8;return folder,dll,function


def main():
    folder,dll,function=compile_helper();source=(ROOT/'input/original.sms').read_bytes()
    low=(c.c_uint8*32768).from_buffer_copy(source[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(source[0x18000:0x1c000])
    reference=json.loads((ROOT/'analysis/wait_refresh_report.json').read_text())
    archive=ROOT/'analysis/wait-refresh-research-v0183';cases=[];rows=[]
    for row in reference['rows']:
        relative=f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}"
        base=ROOT/relative;region=row['region']
        raw=(base/f'{region}-foreground-phase-records.bin').read_bytes()
        metadata=(base/f'{region}-foreground-m1-records.bin').read_bytes()
        waits=(base/f'{region}-save-wait-records.bin').read_bytes()
        for suffix,data in [('foreground-phase-records.bin',raw),('foreground-m1-records.bin',metadata),('save-wait-records.bin',waits)]:
            assert data==(archive/relative/f'{region}-{suffix}').read_bytes()
        events=json.loads((base/f'{region}-audio-irq-events.json').read_text())
        records={}
        for n in range(len(raw)//800):
            captured=raw[n*800:(n+1)*800];pc,time=struct.unpack_from('<2Q',captured)
            if pc in [0xb95,0xbb3]:records[(pc,time)]=(captured,struct.unpack_from('<Q2I',metadata,n*16))
        for number in range(len(waits)//112):
            w=struct.unpack_from('<14Q',waits,number*112)
            initial,first_meta=records[(0xb95,w[0])];end,end_meta=records[(0xbb3,w[2])]
            phase=struct.unpack_from('<12I',initial,16);end_phase=struct.unpack_from('<12I',end,16)
            before=initial[64:400];sound=initial[400:800];tile_count=0
            if before[0x42]:
                pointer=int.from_bytes(before[0x43:0x45],'little');asset=pointer if pointer<0x8000 else before[0x42]*0x4000+(pointer&0x3fff)
                tile_count=source[asset] or 256
            ram=(c.c_uint8*336).from_buffer_copy(before);audio=(c.c_uint8*400).from_buffer_copy(sound)
            output=(c.c_uint32*18)();trace=(c.c_uint32*96)()
            assert function((c.c_uint32*12)(*phase),first_meta[1],ram,audio,low,bank,tile_count,output,trace),(row['town'],region,number,'rejected')
            tag=(row['town'],row['mask'],region,number)
            assert bytes(audio)==end[400:800],(tag,'audio')
            assert all(ram[i]==end[64+i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23]),(tag,'RAM')
            end_raster=(end_phase[1]*3420+(end_phase[0]-end_phase[2]+0x80000000&0xffffffff)-0x80000000)%(phase[3]*3420)
            assert output[0]==end_raster and output[2]==w[2]-w[0],(tag,'phase/time',list(output),end_raster,w[2]-w[0])
            assert output[5]*15==w[3]-w[1] and output[15]==w[4],(tag,'IRQ/polling')
            assert output[10]==end_meta[1] and output[4]+output[6]==end_meta[0]-first_meta[0],(tag,'M1/R')
            assert (output[11],output[13],output[14])==(end_phase[8],end_phase[10],1) and not output[12] and not output[16],(tag,'latches')
            actual=[(e[2]-w[0],bool(e[5])) for e in events if e[1]==0x137 and w[0]<e[2]<w[2]]
            predicted=[(trace[n*6],bool(trace[n*6+5])) for n in range(output[7])]
            assert predicted==actual,(tag,'IRQ entries',predicted,actual)
            cases.append(dict(kind='live',phase=list(phase),refresh=first_meta[1],ram=list(before),audio=list(sound),
                              tile_count=tile_count,expected_ram=list(ram),expected_audio=list(audio),
                              expected=list(output),events=list(trace[:output[7]*6])))
        rows.append(dict(town=row['town'],mask=row['mask'],region=region,cases=len(waits)//112))
        print(row['town'],row['mask'],region,len(waits)//112,'native wait/clock/dynamicIRQ phase,R,331RAM,400audio exact',flush=True)
    (folder/'cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=rows,production_md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                helper_sha256={name:hashlib.sha256((ROOT/'megadrive/src'/f'{name}.c').read_bytes()).hexdigest() for name in MODULES},
                limits=['Original hashed wait entry/return captures. Clock and dynamic native IRQ/audio composed from one entry, with actual IRQ offsets and final phase/R/M1/331RAM/400audio.',
                        'VDP status C01B and joy/pause edges C020..C023 excluded; dummy joy0. Tile count is decoded from original pending asset.',
                        'No production clock wiring, nested IRQs, hardware acknowledgement/waveform/full natural progression claim.'])
    (ROOT/'analysis/native_source_wait_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
