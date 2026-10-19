"""Native68000 differential coverage for the batched FIFO consumer."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from run_core import run

ROOT=Path(__file__).resolve().parents[1]
TEST=r'''
#include "source_psg_queue.h"
volatile u32 bulk_cases,bulk_checks,bulk_failures,bulk_events,bulk_hash=0x12805a80UL;
volatile u16 bulk_done;
static SourcePsgEvent a[512],b[512],input[512],output[513];
static u32 seed=0x1234abcdUL;
static u32 rnd(void) {seed=seed*1664525UL+1013904223UL;return seed;}
#define CHECK(x) do {bulk_checks++;if(!(x)) bulk_failures++;} while(0)
void bulk_test(void) {
 SourcePsgQueue q,r;SourcePsgEvent e;u16 power,turn,i,n,limit,expected,got,origin;u32 time,now;
 for(power=0;power<10;power++) for(turn=0;turn<64;turn++) {
  u16 capacity=1<<power;
  CHECK(!source_psg_queue_init(&q,a,capacity));CHECK(!source_psg_queue_init(&r,b,capacity));
  origin=turn&1?65530:(u16)rnd();q.read=q.write=r.read=r.write=origin;
  n=(rnd()>>16)%(capacity+1);time=rnd();
  for(i=0;i<n;i++) {time+=(rnd()>>16)%10000;input[i].due=time;input[i].value=(u8)rnd();}
  CHECK(!source_psg_queue_push(&q,input,n));CHECK(!source_psg_queue_push(&r,input,n));
  now=time-(rnd()>>16)%20000;limit=(rnd()>>16)%514;
  for(i=0;i<513;i++) {output[i].due=0xa5a5a5a5UL;output[i].value=0xa5;}
  got=0x5aa5;CHECK(!source_psg_queue_take_many(&q,now,output,limit,&got));expected=0;
  while(expected<limit && !source_psg_queue_take(&r,now,&e)) {
   CHECK(expected<got && output[expected].due==e.due && output[expected].value==e.value);
   bulk_hash=(bulk_hash<<1)^(bulk_hash>>31)^e.due^e.value;expected++;
  }
  CHECK(got==expected && q.read==r.read && q.write==r.write);
  for(i=got;i<513;i++) CHECK(output[i].due==0xa5a5a5a5UL && output[i].value==0xa5);
  bulk_events+=got;bulk_cases++;
 }
 CHECK(!source_psg_queue_init(&q,a,8));got=0x5aa5;output[0].due=0x11223344UL;
 q.write=9;CHECK(source_psg_queue_take_many(&q,0,output,8,&got)==1 && got==0x5aa5 && q.read==0 && q.write==9 && output[0].due==0x11223344UL);
 q.write=0;CHECK(source_psg_queue_take_many(&q,0,0,8,&got)==1 && got==0x5aa5);
 CHECK(source_psg_queue_take_many(&q,0,output,8,0)==1 && got==0x5aa5);
 CHECK(source_psg_queue_take_many(0,0,output,8,&got)==1 && got==0x5aa5);
 CHECK(!source_psg_queue_take_many(&q,0,0,0,&got) && !got && !q.read);
 bulk_done=1;
}
'''


def main():
    folder=ROOT/'validation/md-psg-bulk';src=folder/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'test.h').write_text(TEST)
    (src/'source_psg_queue.h').write_text('#include "../../../megadrive/src/source_psg_queue.h"\n')
    (src/'source_psg_queue.c').write_text('#include "../../../megadrive/src/source_psg_queue.c"\n')
    (folder/'host.c').write_text('#ifndef SGDK_GCC\n#include "src/test.h"\n#endif\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),str(folder/'host.c'),str(ROOT/'megadrive/src/source_psg_queue.c'),'-o',str(folder/'host.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'host.dll'));dll.bulk_test()
    names=['cases','checks','failures','events','hash']
    host={n:c.c_uint32.in_dll(dll,'bulk_'+n).value for n in names};assert host['cases']==640 and not host['failures'],host
    print('Host',host,flush=True)
    (src/'main.c').write_text('#include <genesis.h>\n#include "test.h"\nint main(bool hard_reset) {(void)hard_reset;VDP_setEnable(FALSE);SYS_disableInts();bulk_test();while(TRUE) {}return 0;}\n')
    env['PATH']=str(sdk/'bin')+';'+env['PATH'];temp=folder/'compiler-tmp';temp.mkdir(exist_ok=True)
    for key in ['TMP','TEMP','TMPDIR']:env[key]=temp.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=folder,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (folder/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};results=[]
    for region in ['ntsc','pal']:
        observed={}
        def observe(frame,ram):
            def value(n,width):return int.from_bytes(bytes(ram[(symbols['bulk_'+n]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('done',2),**{n:value(n,4) for n in names})
        with contextlib.redirect_stdout(io.StringIO()):run(folder/'out/release/rom.bin',20000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and {n:observed[n] for n in names}==host,observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(host=host,results=results,kernel_sha256=hashlib.sha256((folder/'out/release/rom.bin').read_bytes()).hexdigest(),sources={n:hashlib.sha256((ROOT/'megadrive/src'/n).read_bytes()).hexdigest() for n in ['source_psg_queue.c','source_psg_queue.h']},limits=['640 differential batch/single take cases per native region, capacities1..512, partial/future/empty/zero output capacity, u16cursor/u32dates, preserved output suffix and invalid atomicity. Hash/check/event counts match the same semantic host execution.', 'No concurrent host-thread or native IRQ-preemption proof. Live source-loader output timing and checkpoints tested separately.'])
    (ROOT/'analysis/md_psg_bulk_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
