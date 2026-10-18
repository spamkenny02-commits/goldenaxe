"""Fast repeat arithmetic versus immutable original clock implementation."""
import ctypes as c
import hashlib
import json
import os
import subprocess
from actor_reference import ROOT
WRAPPER='''#include "source_clock.h"
#include "source_rng.h"
u16 reference_clock_repeat(SourceClock*,u16,u8,u16);
u8 reference_clock_execute(SourceClock*,u16,u8,u8,SourceClockInterrupt,void*);
static void dump(const SourceClock *p,u32 *o)
{
 o[0]=p->period;o[1]=p->raster;o[2]=p->until_vint;o[3]=p->elapsed;
 o[4]=p->foreground_tstates;o[5]=p->foreground_m1;o[6]=p->irq_tstates;o[7]=p->irq_m1;
 o[8]=p->irq_count;o[9]=p->status_suppressions;o[10]=p->vector_coalescences;
 o[11]=p->refresh;o[12]=p->iff;o[13]=p->blocked;o[14]=p->pending;o[15]=p->first;
}
u8 repeat_pair(u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,u8 blocked,u8 first,u16 ticks,u16 m1,u16 reps,u32 *out)
{
 SourceClock a,b;
 if(!source_clock_init(&a,lines,raster,refresh,iff,blocked,pending)) return 0;
 a.first=first;a.elapsed=a.foreground_tstates=a.foreground_m1=0xffffff00UL;b=a;
 if(reps==65534) {out[0]=source_clock_plain(&a,ticks,(u8)m1,0,0);out[1]=reference_clock_execute(&b,ticks,(u8)m1,SOURCE_CLOCK_NONE,0,0);}
 else {out[0]=reps==1?source_clock_block(&a,ticks,m1):source_clock_repeat(&a,ticks,m1,reps);out[1]=reference_clock_repeat(&b,ticks,(reps==1 && m1)?1:(u8)m1,reps);}
 if(reps==1 && out[1]) {b.foreground_m1+=m1-1;b.refresh=source_refresh_advance(b.refresh,m1-1);}
 dump(&a,out+2);dump(&b,out+18);return 1;
}
'''

def main():
    folder=ROOT/'validation/clock-repeat-fast';folder.mkdir(exist_ok=True)
    reference=ROOT/'analysis/native-room-finish-v0198/megadrive/src/source_clock.c';source=reference.read_text()
    for name in ['init','execute','checkpoint','repeat_disabled','repeat']:source=source.replace(f'source_clock_{name}(',f'reference_clock_{name}(')
    (folder/'reference.c').write_text(source);(folder/'wrapper.c').write_text(WRAPPER)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'reference.c'),str(folder/'wrapper.c'),str(ROOT/'megadrive/src/source_clock.c'),str(ROOT/'megadrive/src/source_rng.c'),'-o',str(folder/'repeat.dll')],env=env,capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'repeat.dll'));fn=dll.repeat_pair
    fn.argtypes=[c.c_uint16,c.c_uint32,*([c.c_uint8]*5),c.c_uint16,c.c_uint16,c.c_uint16,c.POINTER(c.c_uint32)];fn.restype=c.c_uint8;cases=[]
    for lines in [262,313]:
        for raster in [0,193*3420-1,193*3420,193*3420+1,lines*3420-1,lines*3420-1000,lines*1710,193*3420-1000]:
            for refresh in [0,127,128,255]:
                for iff,pending,blocked,first in [(1,0,0,0),(1,1,0,0),(0,0,0,0),(1,0,1,0),(1,0,0,1)]:
                    for ticks,m1,reps in [(1,1,65535),(3,2,23788),(29,3,127),(135,19,63),(4368,255,65535),(4369,255,65535),(4370,255,65535),(65535,255,65535),(65535,255,1),(1,1,1),(29,3,1),(135,19,1),(0,3,1),(29,0,1),(34615,4879,1),(64,65535,1),(1,256,1),(29,32768,1),(4,1,65534),(65535,255,65534),(0,1,65534),(4,0,65534),(0,3,10),(29,0,10),(29,3,0)]:
                        values=[lines,raster,refresh,iff,pending,blocked,first,ticks,m1,reps];output=(c.c_uint32*34)();assert fn(*values,output)
                        assert output[0]==output[1] and list(output[2:18])==list(output[18:]),(values,list(output))
                        cases.append(dict(inputs=values,accepted=output[0],expected=list(output[2:18])))
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    report=dict(cases=len(cases),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),header_sha256=hashlib.sha256((ROOT/'megadrive/src/source_clock.h').read_bytes()).hexdigest(),module_sha256=hashlib.sha256((ROOT/'megadrive/src/source_clock.c').read_bytes()).hexdigest(),
                limits=['Host bitwise state/return parity with immutable pre-optimization repeat; all guard classes,frame/VINT boundaries,counter/R wrap,max16-bit arithmetic.','Repetition marker65534 selects ordinary instruction fast-path versus immutable execute,including failed pending-IRQ callbacks; block fetch counts extend to65535.','Independent original source and compiled68000 loading chain comparisons remain separate.'])
    (ROOT/'analysis/clock_repeat_fast_report.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'repeat cases exact against immutable clock.')

if __name__=='__main__':main()
