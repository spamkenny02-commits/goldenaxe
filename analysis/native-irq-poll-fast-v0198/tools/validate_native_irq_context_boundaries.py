"""Verify dynamic IRQ adapter diagnostics and successful callback publication."""
import ctypes as c
import hashlib
import json
import os
import subprocess
from actor_reference import ROOT
from validate_native_source_wait import MODULES

WRAPPER='''#include "source_irq_context.h"
typedef struct {u32 writes,traces;} Observer;
static void sink(void *context,const u8 *writes,u16 count)
{Observer *p=(Observer *)context;(void)writes;p->writes+=count;}
static void trace(void *context,const SourceClockIrq *entry,const SourceClockWork *work)
{Observer *p=(Observer *)context;(void)entry;(void)work;p->traces++;}
u8 context_case(u8 kind,const u8 *low,const u8 *bank,u32 *out)
{
 u8 ram[336]={0},audio[400]={0},accepted;SourceIrqContext ctx={0};SourceClockWork work;
 SourceClockIrq entry={193UL*3420+72UL*15,72UL*15,7};Observer observer={0};
 ram[0x2e]=1;ram[0x33]=1;ram[0x35]=0xdd;ram[0x1c]=2;ram[0x30]=2;ram[0x2f]=255;
 audio[5]=128;audio[1]=2;ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.bank6=bank;ctx.low_bytes=32768;
 ctx.input.lines=262;ctx.input.reset_mask=16;ctx.input.joy=17;
 ctx.sink=sink;ctx.sink_context=&observer;ctx.trace=trace;ctx.trace_context=&observer;
 if(kind==0) {ram[0x34]=0x50;ram[0x35]=0xc0;}
 if(kind==1) audio[5]=0x8e;
 if(kind==2) ctx.input.reset_mask=0;
 if(kind==3) {ram[80]=2;ram[0x34]=5;}
 if(kind==4) {ram[0x2e]=0;audio[6]=0x81;}
 if(kind==5) audio[6]=0x81;
 if(kind==6) ctx.input.lines=263;
 accepted=source_irq_interrupt(&ctx,&entry,&work);
 out[0]=accepted;out[1]=ctx.error;out[2]=work.tstates;out[3]=work.fetches;
 out[4]=observer.writes;out[5]=observer.traces;out[6]=ram[0x2e];out[7]=ram[0x1c];
 out[8]=ram[0x30];out[9]=ram[0x2f];out[10]=audio[1];out[11]=ctx.last_irq.reset_requested;
 return 1;
}
'''


def main():
    folder=ROOT/'validation/native-irq-context-boundaries';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'wrapper.c')]
    args.extend(str(ROOT/'megadrive/src'/f'{name}.c') for name in MODULES)
    args.extend(['-o',str(folder/'context.dll')])
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'context.dll'));function=dll.context_case
    function.argtypes=[c.c_uint8,c.POINTER(c.c_uint8),c.POINTER(c.c_uint8),c.POINTER(c.c_uint32)];function.restype=c.c_uint8
    source=(ROOT/'input/original.sms').read_bytes();low=(c.c_uint8*32768).from_buffer_copy(source[:32768]);bank=(c.c_uint8*16384).from_buffer_copy(source[0x18000:0x1c000]);rows=[]
    for kind in range(7):
        output=(c.c_uint32*12)();assert function(kind,low,bank,output)
        if kind in [0,1,2,3,6]:
            assert list(output[:4])==[0,{0:0x800,1:0x18e,2:0x801,3:0x802,6:0x800}[kind],0,0]
            assert not output[5] and output[6]==1 and output[8]==2 and output[9]==255
            assert output[7]==(1 if kind==2 else 2) and output[10]==(2 if kind in [0,6] else 1)
            assert output[11]==(kind==2)
        else:
            assert output[0]==1 and not output[1] and output[2]>500 and output[3]>50 and output[4] and output[5]==1
            assert output[6]==0 and output[8]==1 and output[9]==(255 if kind==4 else 0)
            assert output[7]==(2 if kind==4 else 1)
        rows.append(dict(kind=kind,result=list(output)))
    report=dict(cases=rows,context_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq_context.c').read_bytes()).hexdigest(),
                limits=['Host adapter contracts: invalid graphics/region, unsupported audio, reset and nested IRQ diagnostics; full/audio-only successful state and sink/trace publication.',
                        'Errors return invalid zero work and do not fabricate a frame budget. Streaming audio may already have advanced on later failure. Not source reset/nested emulation proof.'])
    (ROOT/'analysis/native_irq_context_boundaries_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(len(rows),'native IRQ adapter guard/publication cases passed')


if __name__=='__main__':main()
