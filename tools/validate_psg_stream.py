"""Sidecar FIFO/stream backpressure, cancellation and real VINT consumption."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import os
import re
import subprocess
from actor_reference import ROOT
from run_core import run

TEST=r'''
#include "source_psg_stream.h"
volatile u32 gaw_stream_checks,gaw_stream_failures,gaw_stream_failure_line,gaw_stream_produced;
volatile u16 gaw_stream_done;
#define CHECK(x) do {gaw_stream_checks++;if(!(x)) {gaw_stream_failures++;if(!gaw_stream_failure_line) gaw_stream_failure_line=__LINE__;}} while(0)
static SourcePsgEvent storage[8],other[8],incoming[16];
static u8 values[16];static u32 times[16];
static SourcePsgQueue queue;
static SourcePsgStream stream;
static u32 consumed,produced,pumps,origin=0xffff0000UL;
static u32 random_state=0x5932ab41;
static u32 random_word(void) {random_state=random_state*1664525UL+1013904223UL;return random_state;}
static void one(void)
{
 SourcePsgEvent event;u32 due=origin+consumed*21;
 event.due=0x12345678;event.value=0xcc;
 CHECK(source_psg_queue_take(&queue,due-1,&event)==SOURCE_PSG_QUEUE_WAIT);
 CHECK(event.due==0x12345678 && event.value==0xcc);
 CHECK(source_psg_queue_take(&queue,due,&event)==SOURCE_PSG_QUEUE_OK);
 CHECK(event.due==due && event.value==(u8)(consumed^0x5a));consumed++;
}
static u8 pump(void *context) {(void)context;pumps++;one();return 1;}
static u8 cancel(void *context) {(void)context;pumps++;return 0;}
static void run_tests(void)
{
 SourcePsgQueue reference;SourcePsgStream before;SourcePsgEvent a,b,saved[8];
 u32 turn,now=0xffff8000UL,previous;u16 count,n,head,tail;u8 typed,side;
 CHECK(source_psg_queue_push_bytes(0,0,0,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,storage,8)==0);
 CHECK(source_psg_queue_init(&reference,other,8)==0);
 CHECK(source_psg_queue_push_bytes(&queue,0,0,0)==0);
 CHECK(source_psg_queue_push_bytes(&queue,0,times,1)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_push_bytes(&queue,values,0,1)==SOURCE_PSG_QUEUE_INVALID);
 for(turn=0;turn<60000;turn++)
 {
  if(random_word()&1)
  {
   count=(random_word()>>8)%17;previous=reference.write!=reference.read?other[(reference.write-1)&7].due:now;
   for(n=0;n<count;n++) {previous+=random_word()&15;times[n]=previous;values[n]=(u8)random_word();incoming[n].due=times[n];incoming[n].value=values[n];}
   if(count>1 && (random_word()&7)==0) times[count-1]=incoming[count-1].due=times[0]-1;
   head=queue.write;tail=queue.read;for(n=0;n<8;n++) saved[n]=storage[n];
   typed=source_psg_queue_push(&reference,incoming,count);side=source_psg_queue_push_bytes(&queue,values,times,count);CHECK(typed==side);
   if(side) {CHECK(queue.write==head && queue.read==tail);for(n=0;n<8;n++) CHECK(storage[n].due==saved[n].due && storage[n].value==saved[n].value);}
  }
  else
  {
   now+=random_word()&31;a.due=b.due=123;a.value=b.value=77;
   typed=source_psg_queue_take(&reference,now,&a);side=source_psg_queue_take(&queue,now,&b);CHECK(typed==side && a.due==b.due && a.value==b.value);
  }
  CHECK(queue.write==reference.write && queue.read==reference.read);
  for(n=0;n<8;n++) CHECK(storage[n].due==other[n].due && storage[n].value==other[n].value);
 }
 CHECK(source_psg_queue_init(&queue,storage,8)==0);
 CHECK(source_psg_stream_init(0,&queue,pump,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_stream_init(&stream,0,pump,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_stream_init(&stream,&queue,0,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_stream_init(&stream,&queue,pump,0)==0);
 source_psg_stream_sink(&stream,0,0,0);CHECK(!stream.error && !stream.published && !stream.waits);
 for(turn=0;turn<20000;turn++)
 {
  count=1+((turn*7)%8);
  for(n=0;n<count;n++) {times[n]=origin+(produced+n)*21;values[n]=(u8)((produced+n)^0x5a);}
  source_psg_stream_sink(&stream,values,times,count);produced+=count;
  CHECK(!stream.error && stream.published==produced);
 }
 while(consumed<produced) one();
 CHECK(produced>65536 && consumed==produced && stream.waits==pumps && pumps);
 CHECK(queue.read==queue.write && queue.write==(u16)produced);gaw_stream_produced=produced;
 /* A cancelled packet is never partially visible; error fences later calls. */
 CHECK(source_psg_queue_init(&queue,storage,8)==0);
 CHECK(source_psg_stream_init(&stream,&queue,cancel,0)==0);
 for(n=0;n<8;n++) {times[n]=n;values[n]=n;}
 CHECK(source_psg_queue_push_bytes(&queue,values,times,8)==0);
 before=stream;CHECK(source_psg_stream_init(&stream,&queue,pump,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(stream.queue==before.queue && stream.pump==before.pump && stream.error==before.error && stream.published==before.published);
 times[0]=8;source_psg_stream_sink(&stream,values,times,1);
 CHECK(stream.error==SOURCE_PSG_STREAM_CANCELLED && stream.waits==1 && !stream.published && queue.write==8 && queue.read==0);
 source_psg_stream_sink(&stream,values,times,1);CHECK(stream.waits==1 && queue.write==8);
 while(source_psg_queue_take(&queue,100,&a)==0) {}
 CHECK(source_psg_stream_init(&stream,&queue,pump,0)==0);
 times[0]=10;times[1]=9;source_psg_stream_sink(&stream,values,times,2);
 CHECK(stream.error==SOURCE_PSG_QUEUE_ORDER && queue.write==queue.read && !stream.published && !stream.waits);
 CHECK(source_psg_stream_init(&stream,&queue,pump,0)==0);
 source_psg_stream_sink(&stream,0,times,1);CHECK(stream.error==SOURCE_PSG_QUEUE_INVALID && queue.write==queue.read);
 CHECK(source_psg_stream_init(&stream,&queue,pump,0)==0);
 source_psg_stream_sink(&stream,values,times,513);CHECK(stream.error==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_stream_init(&stream,&queue,pump,0)==0);
 source_psg_stream_sink(&stream,values,times,9);CHECK(stream.error==SOURCE_PSG_QUEUE_FULL && !stream.waits && queue.write==queue.read);
}
'''

IRQ=r'''
static SourcePsgQueue irq_queue;static SourcePsgStream irq_stream;
static SourcePsgEvent irq_storage[16];static u8 irq_values[7];static u32 irq_due[7],irq_start;
volatile u32 gaw_irq_sent,gaw_irq_consumed,gaw_irq_failures,gaw_irq_vints;
static void consume(void)
{
 SourcePsgEvent e;u8 result,last=1;u16 count=0;u32 now=vtimer;
 gaw_irq_vints++;
 if(irq_stream.error) {gaw_irq_failures++;return;}
 while((result=source_psg_queue_take(&irq_queue,now,&e))==0)
 {
  if((e.value&127)!=(gaw_irq_consumed&127) || e.due>now) gaw_irq_failures++;
  gaw_irq_consumed++;last=e.value&128;count++;
 }
 if((result!=SOURCE_PSG_QUEUE_EMPTY && result!=SOURCE_PSG_QUEUE_WAIT) || (count && !last)) gaw_irq_failures++;
}
static u8 irq_pump(void *context) {(void)context;SYS_doVBlankProcess();return vtimer-irq_start<5000;}
static void run_irq(void)
{
 u16 n,count;source_psg_queue_init(&irq_queue,irq_storage,16);
 source_psg_stream_init(&irq_stream,&irq_queue,irq_pump,0);
 VDP_setVInterrupt(TRUE);SYS_setVIntCallback(consume);SYS_enableInts();irq_start=vtimer;
 while(gaw_irq_sent<12000UL && vtimer-irq_start<5000UL && !irq_stream.error)
 {
  count=1+(gaw_irq_sent%7);if(count>12000UL-gaw_irq_sent) count=12000UL-gaw_irq_sent;
  for(n=0;n<count;n++) {irq_due[n]=vtimer+2;irq_values[n]=((gaw_irq_sent+n)&127)|(n+1==count?128:0);}
  source_psg_stream_sink(&irq_stream,irq_values,irq_due,count);
  if(!irq_stream.error) gaw_irq_sent+=count;
 }
 while(gaw_irq_consumed<gaw_irq_sent && vtimer-irq_start<5000UL) SYS_doVBlankProcess();
 SYS_disableInts();SYS_setVIntCallback(0);
 if(gaw_irq_sent!=12000UL || gaw_irq_consumed!=12000UL || irq_stream.error || !irq_stream.waits) gaw_irq_failures++;
 gaw_stream_done=1;SYS_enableInts();
}
'''


def main():
    base=ROOT/'validation/psg-stream';src=base/'src';src.mkdir(parents=True,exist_ok=True);(src/'test.h').write_text(TEST)
    (base/'host.c').write_text('#ifndef SGDK_GCC\n#include "src/test.h"\nvoid stream_test(void) {run_tests();}\n#endif\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    modules=['source_psg_queue','source_psg_stream']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(base/'host.c')]+[str(ROOT/'megadrive/src'/(name+'.c')) for name in modules]+['-o',str(base/'host.dll')]
    built=subprocess.run(args,env=env,capture_output=True,text=True);(base/'host-build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(base/'host.dll'));dll.stream_test();host={name:c.c_uint32.in_dll(dll,'gaw_stream_'+name).value for name in ['checks','failures','failure_line','produced']};assert not host['failures'],host;print('Host',host,flush=True)
    for name in modules:(src/(name+'.c')).write_text('#include "../../../megadrive/src/'+name+'.c"\n')
    (src/'source_psg_stream.h').write_text('#include "../../../megadrive/src/source_psg_stream.h"\n')
    (src/'main.c').write_text('#include <genesis.h>\n#include "test.h"\n'+IRQ+'\nint main(bool hard_reset) {VDP_setEnable(FALSE);SYS_disableInts();run_tests();run_irq();while(TRUE) SYS_doVBlankProcess();return 0;}\n')
    env['PATH']=str(sdk/'bin')+';'+env['PATH'];temporary=base/'compiler-tmp';temporary.mkdir(exist_ok=True)
    for key in ['TMPDIR','TMP','TEMP']:env[key]=temporary.resolve().as_posix()
    path=sdk.as_posix();unix='/'+path[0].lower()+path[2:]
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))};rom=base/'out/release/rom.bin';results=[]
    for region in ['auto','pal']:
        observed={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            observed.update(frame=frame,done=value('gaw_stream_done',2),**{name:value('gaw_stream_'+name,4) for name in ['checks','failures','failure_line','produced']},**{name:value('gaw_'+name,4) for name in ['irq_sent','irq_consumed','irq_failures','irq_vints']})
        with contextlib.redirect_stdout(io.StringIO()):run(rom,20000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(observed.get('done')))
        assert observed.get('done') and all(observed[k]==host[k] for k in host) and observed['irq_sent']==observed['irq_consumed']==12000 and not observed['irq_failures'],observed
        results.append(dict(region=region,**observed));print(results[-1],flush=True)
    report=dict(host=host,results=results,kernel_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),sources={name:hashlib.sha256((ROOT/'megadrive/src'/(name+'.c')).read_bytes()).hexdigest() for name in modules},
        limits=['Sidecar pushes match retained typed FIFO semantics; stream checks independent byte/deadline order with32-bit deadline and16-bit cursor wrap,whole-packet retry,cancel/sticky faults and invalid setup.',
                '12000 events additionally pass real emulated VINT consumption while the main producer blocks/retries complete packets. Frame ticks are a test clock only; no physical PSG pacing,source-reader integration or per-byte hardware latency proof.'])
    (ROOT/'analysis/psg_stream_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
