"""Deadline FIFO contract on host and compiled68000, including both wraps."""
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
#include "source_psg_queue.h"
volatile u32 gaw_psg_checks,gaw_psg_failures,gaw_psg_failure_line,gaw_psg_produced;
volatile u16 gaw_psg_done;
#define CHECK(x) do {gaw_psg_checks++;if(!(x)) {gaw_psg_failures++;if(!gaw_psg_failure_line) gaw_psg_failure_line=__LINE__;}} while(0)
static SourcePsgEvent storage[16],batch[16],reference[16];
static u32 random_state=0x67ab1359;
static u32 random_word(void) {random_state=random_state*1664525UL+1013904223UL;return random_state;}
static void run_tests(void)
{
 SourcePsgQueue queue={0},old;SourcePsgEvent out;u16 n,k,capacity,status,len,count,i;
 u32 iteration,now,deadline,origin=0xffffff00UL,produced=0;u16 head,tail;
 CHECK(source_psg_queue_init(0,storage,8)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,0,8)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,storage,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,storage,3)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,storage,65535)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_push(&queue,0,0)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_take(&queue,0,&out)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_init(&queue,storage,8)==SOURCE_PSG_QUEUE_OK);
 old=queue;CHECK(source_psg_queue_init(&queue,storage,3)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(queue.events==old.events && queue.read==old.read && queue.write==old.write && queue.capacity==old.capacity && queue.mask==old.mask);
 CHECK(source_psg_queue_push(&queue,0,0)==SOURCE_PSG_QUEUE_OK);
 CHECK(source_psg_queue_push(&queue,0,1)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_take(&queue,0,0)==SOURCE_PSG_QUEUE_INVALID);
 out.due=123;out.value=0x5a;CHECK(source_psg_queue_take(&queue,0,&out)==SOURCE_PSG_QUEUE_EMPTY);
 CHECK(out.due==123 && out.value==0x5a);
 batch[0].due=0xfffffffeUL;batch[0].value=0x81;batch[1].due=1;batch[1].value=0x42;
 CHECK(source_psg_queue_push(&queue,batch,2)==SOURCE_PSG_QUEUE_OK);
 CHECK(source_psg_queue_take(&queue,0xfffffffdUL,&out)==SOURCE_PSG_QUEUE_WAIT);
 CHECK(source_psg_queue_take(&queue,0xfffffffeUL,&out)==SOURCE_PSG_QUEUE_OK && out.value==0x81 && out.due==0xfffffffeUL);
 CHECK(source_psg_queue_take(&queue,0xffffffffUL,&out)==SOURCE_PSG_QUEUE_WAIT);
 CHECK(source_psg_queue_take(&queue,1,&out)==SOURCE_PSG_QUEUE_OK && out.value==0x42 && out.due==1);
 CHECK(source_psg_queue_take(&queue,1,&out)==SOURCE_PSG_QUEUE_EMPTY);
 batch[0].due=50;batch[1].due=49;head=queue.write;tail=queue.read;
 for(n=0;n<8;n++) {storage[n].due=100+n;storage[n].value=n;}
 CHECK(source_psg_queue_push(&queue,batch,2)==SOURCE_PSG_QUEUE_ORDER);
 CHECK(queue.write==head && queue.read==tail);
 for(n=0;n<8;n++) CHECK(storage[n].due==100UL+n && storage[n].value==n);
 /* A single event repeatedly crosses the16-bit producer/consumer cursors. */
 CHECK(source_psg_queue_init(&queue,storage,1)==SOURCE_PSG_QUEUE_OK);
 for(iteration=0;iteration<70000UL;iteration++)
 {
  batch[0].due=origin+iteration;batch[0].value=(u8)iteration;
  CHECK(source_psg_queue_push(&queue,batch,1)==SOURCE_PSG_QUEUE_OK);
  CHECK(source_psg_queue_push(&queue,batch,1)==SOURCE_PSG_QUEUE_FULL);
  CHECK(source_psg_queue_take(&queue,origin+iteration,&out)==SOURCE_PSG_QUEUE_OK);
  CHECK(out.due==origin+iteration && out.value==(u8)iteration);produced++;
 }
 CHECK(queue.read==(u16)70000UL && queue.write==(u16)70000UL);
 /* Reference uses relative, nonwrapping times and a shifted linear FIFO. */
 for(capacity=1;capacity<=16;capacity*=2)
 {
  CHECK(source_psg_queue_init(&queue,storage,capacity)==SOURCE_PSG_QUEUE_OK);
  count=0;now=0;
  for(iteration=0;iteration<10000UL;iteration++)
  {
   now+=(random_word()>>28)&7;len=(random_word()>>27)&7;
   deadline=count?reference[count-1].due:now;if(deadline<now) deadline=now;
   for(n=0;n<len;n++) {deadline+=(random_word()>>30);batch[n].due=origin+deadline;batch[n].value=(u8)(produced+n);}
   if(iteration%11==0 && len>1) batch[len-1].due=batch[len-2].due-1;
   head=queue.write;tail=queue.read;
   status=source_psg_queue_push(&queue,batch,len);
   if(len>capacity-count) CHECK(status==SOURCE_PSG_QUEUE_FULL);
   else if(iteration%11==0 && len>1) CHECK(status==SOURCE_PSG_QUEUE_ORDER);
   else
   {
    CHECK(status==SOURCE_PSG_QUEUE_OK);
    for(n=0;n<len;n++) {reference[count+n].due=batch[n].due-origin;reference[count+n].value=batch[n].value;}
    count+=len;produced+=len;
   }
   if(status!=SOURCE_PSG_QUEUE_OK) CHECK(queue.write==head && queue.read==tail);
   for(k=0;k<3;k++)
   {
    out.due=0xabcdef01UL;out.value=0x5a;status=source_psg_queue_take(&queue,origin+now,&out);
    if(!count) CHECK(status==SOURCE_PSG_QUEUE_EMPTY);
    else if(reference[0].due>now) CHECK(status==SOURCE_PSG_QUEUE_WAIT);
    else
    {
     CHECK(status==SOURCE_PSG_QUEUE_OK);
     CHECK(out.due==origin+reference[0].due && out.value==reference[0].value);
     count--;for(i=0;i<count;i++) reference[i]=reference[i+1];
    }
    if(status!=SOURCE_PSG_QUEUE_OK) CHECK(out.due==0xabcdef01UL && out.value==0x5a);
   }
   CHECK((u16)(queue.write-queue.read)==count);
  }
  while(count)
  {
   CHECK(source_psg_queue_take(&queue,origin+reference[0].due,&out)==SOURCE_PSG_QUEUE_OK);
   CHECK(out.due==origin+reference[0].due && out.value==reference[0].value);
   count--;for(i=0;i<count;i++) reference[i]=reference[i+1];
  }
 }
 /* Detect corrupted cursor distance rather than accessing invalid payload. */
 queue.read=0;queue.write=queue.capacity+1;
 CHECK(source_psg_queue_push(&queue,batch,1)==SOURCE_PSG_QUEUE_INVALID);
 CHECK(source_psg_queue_take(&queue,0,&out)==SOURCE_PSG_QUEUE_INVALID);
 gaw_psg_produced=produced;
}
'''

IRQ_TEST=r'''
static SourcePsgQueue irq_queue;
static SourcePsgEvent irq_storage[16],irq_batch[7];
volatile u32 gaw_irq_consumed,gaw_irq_sent,gaw_irq_checks,gaw_irq_failures,gaw_irq_vints;
static void consume(void)
{
 SourcePsgEvent event;u8 result,last=1;u16 count=0;u32 now=vtimer;
 gaw_irq_vints++;
 while((result=source_psg_queue_take(&irq_queue,now,&event))==SOURCE_PSG_QUEUE_OK)
 {
  gaw_irq_checks++;
  if((event.value&127)!=(gaw_irq_consumed&127) || event.due>now) gaw_irq_failures++;
  gaw_irq_consumed++;last=event.value&128;count++;
 }
 gaw_irq_checks++;
 if((result!=SOURCE_PSG_QUEUE_EMPTY && result!=SOURCE_PSG_QUEUE_WAIT) || (count && !last)) gaw_irq_failures++;
}
static void run_irq_test(void)
{
 u16 n,len;u8 result;u32 start,due;
 source_psg_queue_init(&irq_queue,irq_storage,16);
 VDP_setVInterrupt(TRUE);SYS_setVIntCallback(consume);SYS_enableInts();start=vtimer;
 while(gaw_irq_sent<12000UL && vtimer-start<5000UL)
 {
  len=1+(gaw_irq_sent%7);if(len>12000UL-gaw_irq_sent) len=12000UL-gaw_irq_sent;
  due=vtimer+2;
  for(n=0;n<len;n++) {irq_batch[n].due=due;irq_batch[n].value=((gaw_irq_sent+n)&127)|(n+1==len?128:0);}
  result=source_psg_queue_push(&irq_queue,irq_batch,len);
  if(result==SOURCE_PSG_QUEUE_OK) gaw_irq_sent+=len;
  else if(result!=SOURCE_PSG_QUEUE_FULL) {gaw_irq_failures++;break;}
  if(result==SOURCE_PSG_QUEUE_FULL) SYS_doVBlankProcess();
 }
 while(gaw_irq_consumed<gaw_irq_sent && vtimer-start<5000UL) SYS_doVBlankProcess();
 SYS_disableInts();SYS_setVIntCallback(0);
 if(gaw_irq_sent!=12000UL || gaw_irq_consumed!=12000UL) gaw_irq_failures++;
 gaw_psg_done=1;SYS_enableInts();
}
'''

def main():
    base=ROOT/'validation/psg-queue';src=base/'src';src.mkdir(parents=True,exist_ok=True)
    (src/'test.h').write_text(TEST)
    host=base/'host.c';host.write_text('#ifndef SGDK_GCC\n#include "src/test.h"\nvoid psg_queue_test(void) {run_tests();}\n#endif\n')
    sdk=(ROOT.parents[1]/'work/sgdk').resolve();env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-shared','-Wall','-Wextra','-Werror','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(host),str(ROOT/'megadrive/src/source_psg_queue.c'),'-o',str(base/'host.dll')]
    built=subprocess.run(args,capture_output=True,text=True,env=env);assert built.returncode==0,built.stderr
    dll=c.CDLL(str(base/'host.dll'));dll.psg_queue_test()
    checks,failures,line,produced=[c.c_uint32.in_dll(dll,name).value for name in ['gaw_psg_checks','gaw_psg_failures','gaw_psg_failure_line','gaw_psg_produced']]
    assert not failures,(checks,failures,line,produced)
    print('Host',checks,'checks;',produced,'events;',failures,'failures',flush=True)
    class Event(c.Structure):_fields_=[('due',c.c_uint32),('value',c.c_uint8)]
    class Queue(c.Structure):_fields_=[('events',c.POINTER(Event)),('capacity',c.c_uint16),('mask',c.c_uint16),('read',c.c_uint16),('write',c.c_uint16)]
    dll.source_psg_queue_init.argtypes=[c.POINTER(Queue),c.POINTER(Event),c.c_uint16]
    dll.source_psg_queue_push.argtypes=[c.POINTER(Queue),c.POINTER(Event),c.c_uint16]
    dll.source_psg_queue_take.argtypes=[c.POINTER(Queue),c.c_uint32,c.POINTER(Event)]
    for name in ['source_psg_queue_init','source_psg_queue_push','source_psg_queue_take']:getattr(dll,name).restype=c.c_uint8
    large=(Event*32768)();incoming=(Event*32768)(*(Event(0xffffffff,n&255) for n in range(32768)));queue=Queue();event=Event()
    assert dll.source_psg_queue_init(c.byref(queue),large,32768)==0
    for turn in range(3):
        assert dll.source_psg_queue_push(c.byref(queue),incoming,32768)==0
        assert dll.source_psg_queue_push(c.byref(queue),incoming,1)==2
        for n in range(32768):
            assert dll.source_psg_queue_take(c.byref(queue),0,c.byref(event))==0 and (event.due,event.value)==(0xffffffff,n&255)
    assert queue.read==queue.write==32768
    (src/'queue.c').write_text('#include "../../../megadrive/src/source_psg_queue.c"\n')
    (src/'main.c').write_text('#include <genesis.h>\n#include "test.h"\n'+IRQ_TEST+'\nint main(bool hard_reset) {VDP_setEnable(FALSE);SYS_disableInts();run_tests();run_irq_test();while(TRUE) SYS_doVBlankProcess();return 0;}\n')
    (base/'Makefile').write_text('GDK ?= ../../../work/sgdk\ninclude $(GDK)/makefile.gen\n')
    path=str(sdk).replace('\\','/');unix='/'+path[0].lower()+path[2:];env['PATH']=str(sdk/'bin')+';'+env['PATH']
    # Include the public queue header for the shared contract test.
    (src/'source_psg_queue.h').write_text('#include "../../../megadrive/src/source_psg_queue.h"\n')
    built=subprocess.run([str(sdk/'bin/sh.exe'),'-c','export PATH="$2/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" -j2','build',path,unix],cwd=base,env=env,capture_output=True,text=True)
    (base/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr[-2000:]
    symbols={m[2]:int(m[1],16)&65535 for line in (base/'out/release/symbol.txt').read_text().splitlines() if(m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    cartridge=base/'out/release/rom.bin';regions=[]
    for region in ['auto','pal']:
        result={}
        def observe(frame,ram):
            def value(name,width):return int.from_bytes(bytes(ram[(symbols[name]+i)^1] for i in range(width)),'big')
            result.update(frame=frame,done=value('gaw_psg_done',2),checks=value('gaw_psg_checks',4),failures=value('gaw_psg_failures',4),failure_line=value('gaw_psg_failure_line',4),produced=value('gaw_psg_produced',4))
            result.update({name:value('gaw_'+name,4) for name in ['irq_sent','irq_consumed','irq_checks','irq_failures','irq_vints']})
        with contextlib.redirect_stdout(io.StringIO()):
            run(cartridge,20000,base/region,set(),[],skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(result.get('done')))
        assert result.get('done') and result['checks']==checks and result['produced']==produced and not result['failures'],(region,result)
        assert result['irq_sent']==result['irq_consumed']==12000 and not result['irq_failures'],(region,result)
        regions.append(dict(region=region,**result));print(regions[-1],flush=True)
    report=dict(host_checks=checks,host_max_capacity_events=3*32768,produced_events=produced,regions=regions,kernel_sha256=hashlib.sha256(cartridge.read_bytes()).hexdigest(),sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'megadrive/src/source_psg_queue.c',ROOT/'megadrive/src/source_psg_queue.h',src/'test.h',src/'main.c']},limits=['FIFO contract: future/exact/late deadlines,32-bit clock wrap,16-bit cursor wrap,capacities1/2/4/8/16,atomic batch rejection,order/capacity/null/corrupt cursor handling and independent linear-FIFO comparison. Maximum32768-entry capacity separately tested on host only; such a buffer exceeds Mega Drive RAM.','Compiled68000 additionally consumes12000 sequenced events in actual emulated VINT callbacks while the main loop produces variable-sized batches and retries FULL. End-of-batch markers check that an IRQ does not observe a partially published batch. Frame ticks are a test clock only; no physical PSG writes,source-semantic timestamps,subframe delivery latency or real-hardware proof. Playable ROM does not use this queue.'])
    (ROOT/'analysis/psg_queue_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
