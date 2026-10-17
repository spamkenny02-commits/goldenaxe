"""Batch optimization versus the previously verified ordinary clock path."""
import ctypes as c
import hashlib
import itertools
import json
import os
import subprocess
from actor_reference import ROOT

WRAPPER='''#include "source_clock.h"
static void fields(const SourceClock *p,u32 *out)
{
 out[0]=p->raster;out[1]=p->until_vint;out[2]=p->elapsed;out[3]=p->foreground_tstates;out[4]=p->foreground_m1;
 out[5]=p->irq_tstates;out[6]=p->irq_m1;out[7]=p->irq_count;out[8]=p->status_suppressions;out[9]=p->vector_coalescences;
 out[10]=p->refresh;out[11]=p->iff;out[12]=p->blocked;out[13]=p->pending;out[14]=p->first;
}
u8 batch_case(u16 lines,u32 raster,u8 refresh,u8 flags,u16 limit,u32 *out)
{
 SourceClock fast,slow;u16 n,i;
 if(!source_clock_init(&fast,lines,raster,refresh,flags&1,(flags>>1)&1,(flags>>2)&1)) return 0;
 fast.first=(flags>>3)&1;slow=fast;n=source_clock_repeat(&fast,29,3,limit);out[0]=n;
 for(i=0;i<n;i++)
 {
  if(!source_clock_execute(&slow,13,1,SOURCE_CLOCK_NONE,0,0) ||
     !source_clock_execute(&slow,4,1,SOURCE_CLOCK_NONE,0,0) ||
     !source_clock_execute(&slow,12,1,SOURCE_CLOCK_NONE,0,0)) return 0;
 }
 fields(&fast,out+1);fields(&slow,out+16);return 1;
}
'''


def main():
    folder=ROOT/'validation/native-clock-repeat';folder.mkdir(exist_ok=True)
    (folder/'wrapper.c').write_text(WRAPPER);sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ)
    env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),
          str(folder/'wrapper.c'),str(ROOT/'megadrive/src/source_clock.c'),str(ROOT/'megadrive/src/source_rng.c'),'-o',str(folder/'clock_repeat.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(folder/'clock_repeat.dll'));function=dll.batch_case
    function.argtypes=[c.c_uint16,c.c_uint32,c.c_uint8,c.c_uint8,c.c_uint16,c.POINTER(c.c_uint32)];function.restype=c.c_uint8
    checked=0;nonzero=0
    for lines in [262,313]:
        period=lines*3420;edge=193*3420
        rasters=sorted({0,period-1,edge,*[edge-d for d in [1,14,15,16,194,195,434,435,436,869,870,871]]})
        for raster,refresh,flags,limit in itertools.product(rasters,[0,127,128,255],range(16),[0,1,2,100,8192,65535]):
            output=(c.c_uint32*31)();assert function(lines,raster,refresh,flags,limit,output)
            until=edge-raster if raster<edge else period-(raster-edge)
            expected=min(limit,until//435) if flags==1 else 0
            assert output[0]==expected and list(output[1:16])==list(output[16:31]),(lines,raster,refresh,flags,limit,list(output))
            checked+=1;nonzero+=bool(expected)
    report=dict(cases=checked,nonzero_batches=nonzero,clock_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_clock.c').read_bytes()).hexdigest(),
                limits=['Host comparison of stable29T/3M1 blocks to ordinary native13/4/12T execution, all latches/first-fetch and VINT-edge guards.',
                        'Independent original-source end-to-end wait checks are in native_source_wait reports; this test verifies optimization parity, not hardware.'])
    (ROOT/'analysis/native_clock_repeat_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(checked,'repeat guard/ordinary execution cases exact;',nonzero,'nonzero batches')


if __name__=='__main__':main()
