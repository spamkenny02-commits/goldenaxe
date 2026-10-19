#include "md_z80_psg.h"
#define BARRIER() __asm__ volatile ("":::"memory")
typedef char mailbox_size_must_be_10[(sizeof(MdZ80PsgMailbox)==10)?1:-1];

static u16 modulo_lines(u32 line,u16 lines)
{
#ifdef SGDK_GCC
    /* All callers pass at most65535+312: quotient fits16 bits. */
    __asm__("divu.w %1,%0":"+d"(line):"d"(lines):"cc");
    return line>>16;
#else
    return line%lines;
#endif
}

u8 md_z80_psg_init(MdZ80PsgProducer *producer,MdZ80PsgMailbox *mailbox,MdServiceClock *clock)
{
    if(!producer || !mailbox || !clock || clock->stamp!=&mailbox->stamp ||
       (clock->lines!=262 && clock->lines!=313) || clock->counter!=100 || clock->reads ||
       mailbox->head || mailbox->tail || mailbox->busy || mailbox->stamp.error) return MD_Z80_PSG_INVALID;
    producer->mailbox=mailbox;producer->clock=clock;producer->physical_line=producer->counter=100;
    producer->last_due=clock->base;producer->published=0;producer->error=0;return MD_Z80_PSG_OK;
}

u8 md_z80_psg_refresh(MdZ80PsgProducer *producer)
{
    SourceMdPsgReplayClock now;u8 status;u16 advance;
    if(!producer || !producer->mailbox || !producer->clock) return MD_Z80_PSG_INVALID;
    if(producer->error || producer->mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    if(producer->mailbox->busy && !producer->mailbox->grant) return MD_Z80_PSG_WAIT;
    status=md_service_clock_now(producer->clock,&now);
    if(status==MD_SERVICE_WAIT) return MD_Z80_PSG_WAIT;
    if(status!=MD_SERVICE_OK) {producer->error=1;return MD_Z80_PSG_FAULT;}
    advance=(u16)(producer->clock->counter-producer->counter);
    producer->physical_line=modulo_lines((u32)producer->physical_line+advance,producer->clock->lines);
    producer->counter=producer->clock->counter;return MD_Z80_PSG_OK;
}

static void target(u32 offset,u16 counter,u16 physical,u16 lines,u16 *due_line,u8 *v,u8 *h)
{
    u32 packed=offset;u16 advance,remainder,index;
#ifndef SGDK_GCC
    (void)packed;
#endif
#ifdef SGDK_GCC
    /* push validates offset<32760*3420 before reaching this function. */
    __asm__("divu.w %1,%0":"+d"(packed):"d"((u16)3420):"cc");
    advance=(u16)packed;remainder=packed>>16;
    packed=(u16)(remainder+19);
    __asm__("divu.w %1,%0":"+d"(packed):"d"((u16)20):"cc");
    index=(u16)packed;
#else
    advance=offset/3420;remainder=offset%3420;index=(remainder+19)/20;
#endif
    if(index==171) {index=0;advance++;}
    *due_line=counter+advance;
    physical=modulo_lines((u32)physical+advance,lines);
    *v=(physical>(lines==313?258:234)?physical+256-lines:physical)&255;
    index+=133;if(index>=171) index-=171;if(index>=148) index+=85;*h=index;
}

u8 md_z80_psg_push(MdZ80PsgProducer *producer,const SourceMdPsgBlock *blocks,u16 count)
{
    MdZ80PsgMailbox *mailbox;u8 head,used,status,payload[22];u16 n,k,line;u32 previous,last,offset;
    if(!producer || !producer->mailbox || !producer->clock || (count && !blocks) || count>1) return MD_Z80_PSG_INVALID;
    mailbox=producer->mailbox;
    if(producer->counter!=producer->clock->counter) return MD_Z80_PSG_INVALID;
    if(producer->error || mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    head=mailbox->head;used=(u8)(head-mailbox->tail);
    if(used>32) {producer->error=1;return MD_Z80_PSG_FAULT;}
    if(count>32-used) return MD_Z80_PSG_FULL;
    if(!count) return MD_Z80_PSG_OK;
    previous=producer->last_due;
    for(n=0;n<count;n++)
    {
        const SourceMdPsgBlock *b=blocks+n;
        if(!b->count || b->count>16 || (b->spacing!=0 && b->spacing!=315 && b->spacing!=630) ||
           (!b->spacing && b->count!=1) || (b->spacing==630 && b->count>8) ||
           b->skip!=(b->spacing==315?(16-b->count)*18:b->spacing==630?(8-b->count)*40:0)) return MD_Z80_PSG_INVALID;
        if((s32)(b->due-previous)<0) return MD_Z80_PSG_ORDER;
        previous=b->due+(u32)(b->count-1)*b->spacing;
    }
    last=previous;
    if(last-producer->clock->base>=16384UL*3420)
    {
        status=md_z80_psg_refresh(producer);if(status!=MD_Z80_PSG_OK) return status;
    }
    for(n=0;n<count;n++)
        if(blocks[n].due-producer->clock->base>=32760UL*3420 ||
           blocks[n].due+(u32)(blocks[n].count-1)*blocks[n].spacing-producer->clock->base>=32760UL*3420) return MD_Z80_PSG_ORDER;
    for(n=0;n<count;n++)
    {
        const SourceMdPsgBlock *b=blocks+n;u8 v,h,*slot=payload;
        offset=b->due-producer->clock->base;
        target(offset,producer->counter,producer->physical_line,producer->clock->lines,&line,&v,&h);
        slot[0]=line;slot[1]=line>>8;slot[2]=v;slot[3]=h;
        slot[4]=b->spacing==630?2:b->spacing==315?1:0;slot[5]=b->count;
        for(k=0;k<16;k++) slot[6+k]=b->values[k];
    }
    BARRIER();status=md_z80_psg_transfer(mailbox,payload,head&31,(u8)(head+1));
    if(status!=MD_Z80_PSG_OK) return status;
    producer->published+=count;producer->last_due=last;return MD_Z80_PSG_OK;
}
