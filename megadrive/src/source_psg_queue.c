#include "source_psg_queue.h"

/* Publish payload before head, and finish copying before releasing tail. */
#define BARRIER() __asm__ volatile ("":::"memory")

static u8 valid(const SourcePsgQueue *queue)
{
    return queue && queue->events && queue->capacity &&
           queue->capacity<=32768 && !(queue->capacity&(queue->capacity-1)) &&
           queue->mask==queue->capacity-1;
}

u8 source_psg_queue_init(SourcePsgQueue *queue,SourcePsgEvent *storage,u16 capacity)
{
    if(!queue || !storage || !capacity || capacity>32768 || (capacity&(capacity-1)))
        return SOURCE_PSG_QUEUE_INVALID;
    queue->events=storage;queue->capacity=capacity;queue->mask=capacity-1;
    queue->read=queue->write=0;return SOURCE_PSG_QUEUE_OK;
}

u8 source_psg_queue_push(SourcePsgQueue *queue,const SourcePsgEvent *events,u16 count)
{
    u16 head,tail,used,n;u32 previous;
    if(!valid(queue) || (count && !events)) return SOURCE_PSG_QUEUE_INVALID;
    head=queue->write;tail=queue->read;used=(u16)(head-tail);
    if(used>queue->capacity) return SOURCE_PSG_QUEUE_INVALID;
    if(count>queue->capacity-used) return SOURCE_PSG_QUEUE_FULL;
    if(!count) return SOURCE_PSG_QUEUE_OK;
    BARRIER();
    previous=used?queue->events[(head-1)&queue->mask].due:events[0].due;
    for(n=0;n<count;n++)
    {
        if((s32)(events[n].due-previous)<0) return SOURCE_PSG_QUEUE_ORDER;
        previous=events[n].due;
    }
    for(n=0;n<count;n++) queue->events[(head+n)&queue->mask]=events[n];
    BARRIER();queue->write=(u16)(head+count);return SOURCE_PSG_QUEUE_OK;
}

u8 source_psg_queue_take(SourcePsgQueue *queue,u32 now,SourcePsgEvent *event)
{
    u16 head,tail,used;const SourcePsgEvent *next;
    if(!valid(queue) || !event) return SOURCE_PSG_QUEUE_INVALID;
    tail=queue->read;head=queue->write;used=(u16)(head-tail);
    if(used>queue->capacity) return SOURCE_PSG_QUEUE_INVALID;
    if(!used) return SOURCE_PSG_QUEUE_EMPTY;
    BARRIER();next=queue->events+(tail&queue->mask);
    if((s32)(now-next->due)<0) return SOURCE_PSG_QUEUE_WAIT;
    *event=*next;BARRIER();queue->read=(u16)(tail+1);
    return SOURCE_PSG_QUEUE_OK;
}
