#include "md_psg_service.h"

static u8 fault(MdPsgService *service,u16 error)
{service->error=error;return 0;}

u8 md_psg_service_init(MdPsgService *service,MdServiceClock *clock,SourcePsgQueue *queue,u32 epoch,u16 lead)
{
    if(!service || !clock || !clock->stamp || (clock->lines!=262 && clock->lines!=313) ||
       !queue || !queue->events || !queue->capacity || queue->mask!=queue->capacity-1 ||
       (queue->capacity&(queue->capacity-1)) || queue->read!=queue->write || lead<1 || lead>16) return 0;
    service->clock=clock;service->queue=queue;service->epoch=epoch;service->lead=lead;
    service->emitted=service->prepared=service->waits=0;
    service->armed=service->error=service->gate=service->read=service->write=0;return 1;
}

u8 md_psg_service_prepare(MdPsgService *service)
{
    SourcePsgQueue *queue;SourcePsgEvent events[16];u16 read,available,count,spacing,used,index;
    u32 offset,line;
    if(!service || !service->clock || !service->queue) return 0;
    if(service->error) return 0;
    if((u16)(service->write-service->read)>32) return fault(service,1);
    while((u16)(service->write-service->read)<32)
    {
    count=1;spacing=0;
    queue=service->queue;read=queue->read;available=(u16)(queue->write-read);
    if(!available) break;
    if(available>queue->capacity) return fault(service,1);
    events[0]=queue->events[read&queue->mask];
    if(available>1)
    {
        u32 delta=queue->events[(read+1)&queue->mask].due-events[0].due;
        if(delta==315 || delta==630) spacing=(u16)delta;
    }
    if(spacing)
        while(count<available && count<(spacing==315?16:8))
        {
            SourcePsgEvent next=queue->events[(read+count)&queue->mask];
            if(next.due-events[count-1].due!=spacing) break;
            events[count++]=next;
        }
    offset=events[0].due-service->epoch;
    index=service->write&31;
    if(offset>=32760UL*3420 || source_md_psg_plan(events,count,service->blocks+index,1,&used) || used!=1 ||
       source_md_psg_plan_beam(service->blocks+index,1,service->clock->lines,100,service->epoch)) return fault(service,2);
#ifdef SGDK_GCC
    line=offset;
    /* offset<32760*3420 above proves that DIVU's quotient fits16 bits. */
    __asm__("divu.w %1,%0":"+d"(line):"d"((u16)3420):"cc");
    line=(u16)line+100UL;
#else
    line=offset/3420+100;
#endif
    service->gates[index]=(u16)(line-service->lead);
    queue->read=read+count;service->prepared+=count;service->write++;
    }
    service->armed=service->read!=service->write;
    if(service->armed) service->gate=service->gates[service->read&31];
    return 1;
}

u8 md_psg_service_dispatch(MdPsgService *service)
{
    u8 status;u32 spins=0;u16 count=0,groups=1,index;SourceMdPsgBlock *block;
    if(!service || !service->clock || service->error) return 0;
    if(!service->armed) return 1;
    index=service->read&31;block=service->blocks+index;
    do {status=md_service_clock_now(service->clock,&service->physical);service->waits+=status==MD_SERVICE_WAIT;}
    while(status==MD_SERVICE_WAIT && ++spins<100000UL);
    if(status!=MD_SERVICE_OK) return fault(service,3);
    if((s32)(block->due-service->physical.master)>(s32)((u32)(service->lead+1)*3420)) return 1;
    while(groups<(u16)(service->write-service->read) && index+groups<32 &&
          block[groups].due-block[0].due<=60000UL && block[groups].due-block[groups-1].due<=17100UL) groups++;
    for(index=0;index<groups;index++) count+=block[index].count;
    if(source_md_psg_replay_planned(&service->physical,block,groups)) return fault(service,4);
    service->emitted+=count;service->read+=groups;service->armed=service->read!=service->write;
    if(!service->armed) service->read=service->write=0;
    return md_psg_service_prepare(service);
}

u8 md_psg_service_flush(MdPsgService *service)
{
    if(!md_psg_service_prepare(service)) return 0;
    while(service->armed)
    {
        /* Flush is used only at a producer boundary. Bypass the cheap gate,
         * keep fresh clocks while waiting for a potentially distant group. */
        if(!md_psg_service_dispatch(service)) return 0;
    }
    return 1;
}
