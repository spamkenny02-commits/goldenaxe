"""Disabled-IRQ batching preserves slow instruction stepping and guard state."""
import ctypes as c
import json
import os
import subprocess
from actor_reference import ROOT
WRAPPER='''#include "source_clock.h"
static void dump(const SourceClock *p,u32 *o)
{
 o[0]=p->period;o[1]=p->raster;o[2]=p->until_vint;o[3]=p->elapsed;
 o[4]=p->foreground_tstates;o[5]=p->foreground_m1;o[6]=p->irq_tstates;o[7]=p->irq_m1;
 o[8]=p->irq_count;o[9]=p->status_suppressions;o[10]=p->vector_coalescences;
 o[11]=p->refresh;o[12]=p->iff;o[13]=p->blocked;o[14]=p->pending;o[15]=p->first;
}
u8 disabled_case(u16 lines,u32 raster,u8 refresh,u8 pending,u16 count,u32 *out)
{
 SourceClock fast,slow;u16 n;
 if(!source_clock_init(&fast,lines,raster,refresh,0,0,pending)) return 0;
 if(!source_clock_execute(&fast,4,1,SOURCE_CLOCK_NONE,0,0)) return 0;
 slow=fast;
 if(source_clock_repeat_disabled(&fast,29,3,count)!=count) return 0;
 for(n=0;n<count;n++)
  if(!source_clock_execute(&slow,16,2,SOURCE_CLOCK_NONE,0,0) || !source_clock_execute(&slow,13,1,SOURCE_CLOCK_NONE,0,0)) return 0;
 dump(&fast,out);dump(&slow,out+16);return 1;
}
u8 disabled_guard(u8 first,u8 blocked,u8 enabled,u16 ticks,u8 m1,u16 count,u32 *out)
{
 SourceClock clock;u16 accepted;
 source_clock_init(&clock,262,100,127,enabled,blocked,1);clock.first=first;
 dump(&clock,out);accepted=source_clock_repeat_disabled(&clock,ticks,m1,count);dump(&clock,out+16);
 return accepted!=0;
}
'''

def main():
    folder=ROOT/'validation/clock-disabled-repeat';folder.mkdir(exist_ok=True);(folder/'wrapper.c').write_text(WRAPPER)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),
        str(folder/'wrapper.c'),str(ROOT/'megadrive/src/source_clock.c'),str(ROOT/'megadrive/src/source_rng.c'),'-o',str(folder/'repeat.dll')],env=env,capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'repeat.dll'));fn=dll.disabled_case
    fn.argtypes=[c.c_uint16,c.c_uint32,c.c_uint8,c.c_uint8,c.c_uint16,c.POINTER(c.c_uint32)];fn.restype=c.c_uint8
    cases=[]
    for lines in [262,313]:
        for raster in [0,193*3420-1,193*3420,193*3420+1,lines*3420-1,lines*3420-1000,lines*1710,193*3420-1000]:
            for refresh in [0,127,128,255]:
                for pending in [0,1]:
                    for count in [1,2,127,256,4096]:
                        output=(c.c_uint32*32)();assert fn(lines,raster,refresh,pending,count,output)
                        assert list(output[:16])==list(output[16:]),(lines,raster,refresh,pending,count,list(output))
                        cases.append(dict(lines=lines,raster=raster,refresh=refresh,pending=pending,count=count,expected=list(output[:16])))
    guard=dll.disabled_guard;guard.argtypes=[c.c_uint8,c.c_uint8,c.c_uint8,c.c_uint16,c.c_uint8,c.c_uint16,c.POINTER(c.c_uint32)]
    guards=[(1,0,0,29,3,127),(0,1,0,29,3,127),(0,0,1,29,3,127),(0,0,0,0,3,127),(0,0,0,29,0,127),(0,0,0,29,3,0),(0,0,0,65535,255,65535)]
    for args in guards:
        output=(c.c_uint32*32)();assert not guard(*args,output) and list(output[:16])==list(output[16:]),args
    (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (ROOT/'analysis/clock_disabled_repeat_report.json').write_text(json.dumps(dict(cases=len(cases),guards=len(guards),limits=['Host parity with original OUTI16T/2M1 and DJNZ13T/1M1 stepping; late frame/VINT/pending/R and multi-frame spans.','No DI/EI/status inside grouped blocks; new full native scene chain provides independent source checkpoint proof.']),indent=2)+'\n')
    print(len(cases),'disabled spans and',len(guards),'rejection guards exact.')

if __name__=='__main__':main()
