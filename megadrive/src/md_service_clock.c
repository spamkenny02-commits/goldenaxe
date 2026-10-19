#include "md_service_clock.h"
#define BARRIER() __asm__ volatile ("":::"memory")

static u32 line_master(u16 lines)
{
#ifdef SGDK_GCC
    u32 result=lines;
    __asm__("mulu.w %1,%0":"+d"(result):"d"((u16)3420):"cc");
    return result;
#else
    return (u32)lines*3420;
#endif
}

u8 md_service_clock_init(MdServiceClock *clock,MdServiceStamp *stamp,u16 lines,u32 epoch)
{
    if(!clock || !stamp || (lines!=262 && lines!=313)) return MD_SERVICE_INVALID;
    clock->stamp=stamp;clock->base=epoch;clock->counter=100;clock->lines=lines;
    clock->error=0;clock->reads=clock->retries=0;return MD_SERVICE_OK;
}

u8 md_service_clock_now(MdServiceClock *clock,SourceMdPsgReplayClock *output)
{
    MdServiceStamp *stamp;u16 attempt,counter,hv,h,advance;u8 sequence,v,delta;
    u32 base;
    if(!clock || !output || !clock->stamp || (clock->lines!=262 && clock->lines!=313)) return MD_SERVICE_INVALID;
    if(clock->error) return MD_SERVICE_FAULT;
    stamp=clock->stamp;
    if(stamp->error) {clock->error=1;return MD_SERVICE_FAULT;}
    if(!stamp->ready) return MD_SERVICE_WAIT;
    for(attempt=0;attempt<256;attempt++)
    {
        sequence=stamp->sequence;
        if(sequence&1) {clock->retries++;continue;}
        BARRIER();v=stamp->v;counter=(u16)stamp->counter_hi*256+stamp->counter_lo;BARRIER();
        if(sequence!=stamp->sequence) {clock->retries++;continue;}
        hv=md_service_clock_hv();h=hv&255;
        delta=(u8)((hv>>8)-v);
        if(delta>4) delta=(u8)(delta+clock->lines-256);
        /* A future publication can be visible in a scanline-batched emulator.
         * It appears as -1V,not an old<=4line record: retry with fresh HV. */
        if(delta>4) {clock->retries++;continue;}
        if(h>147 && h<233) return MD_SERVICE_INVALID;
        if(h>=233) h-=85;
        if(h<133) h+=171;
        h=(h-133)*20;
        advance=(u16)(counter-clock->counter);base=clock->base;
        if(advance) base+=line_master(advance);
        output->master=base+line_master(delta)+h;
        output->vertical=hv&0xff00;output->horizontal=h;output->lines=clock->lines;output->error=0;
        clock->base=base;clock->counter=counter;clock->reads++;return MD_SERVICE_OK;
    }
    return MD_SERVICE_WAIT;
}
