"""Kernel text for actual 68000 loader -> IRQ FIFO -> Z80 output measurement."""
from validate_md_loading_audio import MAIN as BASE
from validate_queued_loading import wrapper

CONTROLLER = r'''
static MdZ80PsgMailbox mailbox;static MdServiceClock service;static MdZ80PsgProducer producer;
static SourceMdPsgReplayClock physical;
volatile u32 gaw_z80_failure_code,gaw_z80_foreground,gaw_z80_work_count;
volatile u32 gaw_z80_queue_full,gaw_z80_grant_wait,gaw_z80_wrap_head,gaw_z80_wrap_tail,gaw_z80_refresh_counter;
static u8 session_failed;
static void work(void) {gaw_z80_foreground=(gaw_z80_foreground<<1)^((gaw_z80_foreground&0x80000000UL)?0x04c11db7UL:0);gaw_z80_work_count++;}
static void fault(u32 code) {if(!gaw_z80_failure_code) gaw_z80_failure_code=code;session_failed=1;gaw_replay_failures++;}
static u8 fresh(void) {
 u32 spins=0;u8 status;
 do {status=md_service_clock_now(&service,&physical);if(status==MD_SERVICE_WAIT) work();} while(status==MD_SERVICE_WAIT && ++spins<100000UL);
 if(status!=MD_SERVICE_OK) {fault(0x100|status);return 0;}return 1;
}
void cooperative_audio(SourceQueuedIrqContext *queued) {
 SourcePsgQueue *q=queued->stream.queue;u16 n=0,count,k;u32 cutoff,spins;u8 status;
 *(volatile u16*)0xc00010=0x30;
 gaw_replay_callbacks++;
 if(q->read!=q->write) {
  cutoff=q->events[(q->write-1)&q->mask].due;
  while(n<128 && source_psg_queue_take(q,cutoff,stream+n)==0) n++;
  if(q->read!=q->write || captured_count+n>128) fault(0x200);
  else {
   for(count=0;count<n;count++) captured[captured_count++]=stream[count];
   if(source_md_psg_plan(stream,n,blocks,128,&count)) fault(0x300);
   else if(!session_failed) for(k=0;k<count;k++) {
    spins=0;
    do {
     status=md_z80_psg_push(&producer,blocks+k,1);
     if(status==MD_Z80_PSG_FULL) gaw_z80_queue_full++;
     if(status==MD_Z80_PSG_WAIT) gaw_z80_grant_wait++;
     if(status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) work();
    } while((status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) && ++spins<100000UL);
    if(status) {fault(0x400|status);break;}
   }
  }
 }
 *(volatile u16*)0xc00010=0x31;
}
u16 cooperative_collect(u32 *dates,u8 *bytes) {
 u16 n;for(n=0;n<captured_count;n++) {dates[n]=captured[n].due;bytes[n]=captured[n].value;}return captured_count;
}
void cooperative_begin(void) {
 u32 spins=0;u8 status;session_failed=0;
 Z80_requestBus(TRUE);*(volatile u16*)0xc00010=0x80+gaw_replay_cases;
 status=md_z80_psg_start(&mailbox,physical_lines,driver,sizeof(driver));if(status) {fault(0x500|status);return;}
 status=md_service_clock_init(&service,&mailbox.stamp,physical_lines,epoch);if(status) {fault(0x600|status);return;}
 status=md_z80_psg_init(&producer,&mailbox,&service);if(status) {fault(0x700|status);return;}
 SYS_disableInts();
 while(!mailbox.stamp.ready && !mailbox.stamp.error && ++spins<100000UL) work();
 if(!mailbox.stamp.ready || mailbox.stamp.error) fault(0x800|mailbox.stamp.error);
}
void cooperative_finish(void) {
 u32 spins=0;u8 status;
 *(volatile u16*)0xc00010=0x32;
 if(!session_failed && fresh()) gaw_replay_clocks[gaw_replay_cases][0]=physical.master-epoch;
 *(volatile u16*)0xc00010=0x33;
 while((mailbox.head!=mailbox.tail || mailbox.busy) && !mailbox.stamp.error && ++spins<1000000UL) work();
 if(mailbox.head!=mailbox.tail || mailbox.busy || mailbox.stamp.error) {fault(0x900|mailbox.stamp.error);return;}
 if(!session_failed && fresh()) gaw_replay_clocks[gaw_replay_cases][1]=physical.master-epoch;
 gaw_z80_wrap_head=mailbox.head;gaw_z80_wrap_tail=mailbox.tail;gaw_z80_refresh_counter=producer.counter;
 spins=0;do {status=md_z80_psg_stop(&mailbox);if(status==MD_Z80_PSG_WAIT) work();} while(status==MD_Z80_PSG_WAIT && ++spins<100000UL);
 if(status) fault(0xa00|status);
 spins=0;while(mailbox.stamp.ready && ++spins<100000UL) work();
 if(mailbox.stamp.ready) fault(0xb00);
}
'''


def deferred_controller():
    text=CONTROLLER.replace('static u8 session_failed;', 'static u8 session_failed;static u16 pending_read,pending_count;')
    a=text.index('void cooperative_audio(');b=text.index('u16 cooperative_collect(',a)
    text=text[:a]+r'''
static void cooperative_publish(void) {
 u16 k;u8 status;
 if(!session_failed) for(k=pending_read;k<pending_count;k++) {
  status=md_z80_psg_push(&producer,blocks+k,1);
  if(status==MD_Z80_PSG_FULL) gaw_z80_queue_full++;
  if(status==MD_Z80_PSG_WAIT) gaw_z80_grant_wait++;
  if(status==MD_Z80_PSG_FULL || status==MD_Z80_PSG_WAIT) break;
  if(status) {fault(0x400|status);break;}
  pending_read++;
 }
}
void cooperative_service(void) {if(pending_read!=pending_count) cooperative_publish();}
void cooperative_audio(SourceQueuedIrqContext *queued) {
 SourcePsgQueue *q=queued->stream.queue;u16 n=0,count;u32 cutoff;
 *(volatile u16*)0xc00010=0x30;
 gaw_replay_callbacks++;
 if(q->read!=q->write) {
  cutoff=q->events[(q->write-1)&q->mask].due;
  while(n<128 && source_psg_queue_take(q,cutoff,stream+n)==0) n++;
  if(q->read!=q->write || captured_count+n>128) fault(0x200);
  else {
   for(count=0;count<n;count++) captured[captured_count++]=stream[count];
   if(source_md_psg_plan(stream,n,blocks+pending_count,128-pending_count,&count)) fault(0x300);
   else pending_count+=count;
  }
 }
 cooperative_publish();
 *(volatile u16*)0xc00010=0x31;
}
'''+text[b:]
    text=text.replace('u8 status;session_failed=0;', 'u8 status;session_failed=0;pending_read=pending_count=0;')
    text=text.replace(' *(volatile u16*)0xc00010=0x32;', r''' *(volatile u16*)0xc00010=0x32;
 while(pending_read!=pending_count && !session_failed && ++spins<1000000UL) {cooperative_publish();work();}
 if(pending_read!=pending_count) {fault(0xc00);return;}
 spins=0;''')
    return text


def sources(bare=False, packets=False, deferred=False):
    main=BASE.replace('#include "md_service_clock.h"','#include "md_service_clock.h"\n#include "md_z80_psg.h"')
    main=main.replace('gaw_live_', 'gaw_replay_')
    main=main.replace('gaw_replay_bytes,gaw_replay_callbacks;', 'gaw_replay_bytes,gaw_replay_callbacks,gaw_replay_extra_cases;')
    main=main.replace('gaw_replay_times[48][2]', 'gaw_replay_clocks[48][3]')
    main=main.replace('static MdServiceStamp stamp;static MdServiceClock service;static SourceMdPsgReplayClock physical;', '')
    a=main.index('static u8 fresh(void)');b=main.index('int main(bool hard_reset)',a)
    main=main[:a]+(deferred_controller() if deferred else CONTROLLER)+main[b:]
    main=main.replace(' for(row=0;row<24;row++)', ' gaw_replay_extra_cases=0;gaw_z80_foreground=0x8123905UL;\n for(row=0;row<24;row++)')
    main=main.replace('gaw_replay_times[row*2+mode][1]=output[2];','gaw_replay_clocks[row*2+mode][2]=output[2];')
    if packets:
        needle='u16 cooperative_collect(u32 *dates,u8 *bytes) {'
        main=main.replace(needle,'''void cooperative_packet(void *context,const u8 *bytes,const u32 *dates,u16 count) {
 SourceQueuedIrqContext *queued=(SourceQueuedIrqContext *)context;
 source_psg_stream_sink(&queued->stream,bytes,dates,count);
 if(!queued->stream.error) cooperative_audio(queued);
}
'''+needle)
    body=wrapper().replace('static void snapshot(', 'void cooperative_begin(void);void cooperative_finish(void);\nvoid cooperative_audio(SourceQueuedIrqContext *queued);\nvoid cooperative_packet(void *,const u8 *,const u32 *,u16);\nu16 cooperative_collect(u32 *dates,u8 *bytes);\nstatic void snapshot(',1)
    needle=' row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;'
    assert body.count(needle)==1
    if not packets:body=body.replace(needle,needle+'\n cooperative_audio((SourceQueuedIrqContext *)p->irq);')
    else:
        needle=' if(source_irq_queue_bind(&queued,&fifo,progress,&pump)!=0) return 0;'
        assert body.count(needle)==1
        body=body.replace(needle,needle+'\n queued.timed.sink=cooperative_packet;queued.timed.sink_context=&queued;')
    needle=' n=0;\n while(source_psg_queue_take(&fifo,clock.elapsed,&event)==0)\n {if(n>=128) return 0;due[n]=event.due;values[n++]=event.value;}'
    assert body.count(needle)==1
    body=body.replace(needle,' n=cooperative_collect(due,values);')
    body=body.replace('QueuePump pump={0};SourcePsgEvent event;','QueuePump pump={0};')
    needle=' if(!source_graphics_load_class0_planned('
    assert body.count(needle)==1
    body=body.replace(needle,' cooperative_begin();\n'+needle)
    needle=' snapshot(&clock,&queued.timed.core,out);'
    assert body.count(needle)==1
    body=body.replace(needle,' cooperative_finish();\n'+needle)
    if bare:
        a=body.index(' snapshot(clock,ctx,p->snapshots+p->points*18);')
        b=body.index(' p->points++;return 1;',a)
        body=body[:a]+body[b:]
        main=main.replace('  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_replay_failures++;','')
        main=main.replace('  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_replay_failures++;',
            '  for(n=0;n<336;n++) if(ram[n]!=cases[row].states[15*736+n]) gaw_replay_failures++;\n  for(n=0;n<400;n++) if(audio[n]!=cases[row].states[15*736+336+n]) gaw_replay_failures++;')
    return main,body
