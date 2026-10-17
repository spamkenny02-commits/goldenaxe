#include "source_clock.h"
#include "source_rng.h"

static u32 advance(SourceClock *clock,u32 master)
{
    u32 crossings=0;
    clock->elapsed+=master;
    /* Ordinary instructions and supported IRQs fit within one frame.
     * Avoid software 32-bit division on every 68000 instruction step. */
    if(master<clock->period)
    {
        clock->raster+=master;
        if(clock->raster>=clock->period) clock->raster-=clock->period;
        if(master>=clock->until_vint)
        {
            clock->until_vint+=clock->period-master;
            clock->pending=1;
            return 1;
        }
        clock->until_vint-=master;
        return 0;
    }
    clock->raster=(clock->raster+master%clock->period)%clock->period;
    if(master>=clock->until_vint)
    {
        master-=clock->until_vint;
        crossings=1+master/clock->period;
        clock->until_vint=clock->period-master%clock->period;
        clock->pending=1;
    }
    else clock->until_vint-=master;
    return crossings;
}

static u8 boundary(SourceClock *clock,SourceClockInterrupt interrupt,void *context)
{
    u16 guard;
    for(guard=0;guard<64;guard++)
    {
        SourceClockIrq entry;SourceClockWork work;
        if(!clock->pending || !clock->iff || clock->blocked) return 1;
        if(!interrupt) return 0;
        entry.entry_raster=clock->raster+72UL*15;
        if(entry.entry_raster>=clock->period) entry.entry_raster-=clock->period;
        entry.entry_elapsed=clock->elapsed+72UL*15;
        entry.entry_refresh=source_refresh_advance(clock->refresh,7);
        if(!interrupt(context,&entry,&work) || work.tstates<82 ||
           work.tstates>0xffffffffUL/15 || work.fetches<7) return 0;
        /* Status is read after accept13T,PUSH AF11T andIN11T. */
        clock->vector_coalescences+=advance(clock,35UL*15);
        clock->pending=0;
        advance(clock,(work.tstates-35)*15);
        clock->refresh=source_refresh_advance(clock->refresh,work.fetches);
        clock->irq_tstates+=work.tstates;clock->irq_m1+=work.fetches;
        clock->irq_count++;clock->iff=1;clock->blocked=0;
    }
    return 0;
}

u8 source_clock_init(SourceClock *clock,u16 lines,u32 raster,u8 refresh,u8 iff,u8 blocked,u8 pending)
{
    u32 period=(u32)lines*3420;
    if((lines!=262 && lines!=313) || raster>=period || iff>1 || blocked>1 || pending>1) return 0;
    clock->period=period;clock->raster=raster;
    clock->until_vint=raster<193UL*3420?193UL*3420-raster:period-(raster-193UL*3420);
    clock->elapsed=clock->foreground_tstates=clock->foreground_m1=0;
    clock->irq_tstates=clock->irq_m1=clock->irq_count=0;
    clock->status_suppressions=clock->vector_coalescences=0;
    clock->refresh=refresh;clock->iff=iff;clock->blocked=blocked;
    clock->pending=pending;clock->first=1;
    return 1;
}

u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context)
{
    u8 first=clock->first;u32 crossed;
    if(!tstates || !fetches || effect>SOURCE_CLOCK_STATUS) return 0;
    if(!first && !boundary(clock,interrupt,context)) return 0;
    clock->first=0;clock->blocked=0;
    crossed=advance(clock,(u32)tstates*15);
    clock->foreground_tstates+=tstates;clock->foreground_m1+=fetches;
    clock->refresh=source_refresh_advance(clock->refresh,fetches-first);
    if(effect==SOURCE_CLOCK_DI) clock->iff=0;
    else if(effect==SOURCE_CLOCK_EI) { clock->iff=1;clock->blocked=1; }
    else if(effect==SOURCE_CLOCK_STATUS)
    { clock->pending=0;clock->status_suppressions+=crossed; }
    return 1;
}

u8 source_clock_checkpoint(SourceClock *clock,SourceClockInterrupt interrupt,void *context)
{
    if(!boundary(clock,interrupt,context)) return 0;
    clock->blocked=0;clock->first=1;
    clock->refresh=source_refresh_advance(clock->refresh,1);
    return 1;
}

u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions)
{
    u32 count,master;
    if(!tstates || !fetches || !repetitions || clock->first || clock->blocked ||
       clock->pending || !clock->iff) return 0;
    master=(u32)tstates*15;count=clock->until_vint/master;
    if(count>repetitions) count=repetitions;
    if(!count) return 0;
    advance(clock,count*master);
    clock->foreground_tstates+=count*tstates;clock->foreground_m1+=count*fetches;
    clock->refresh=source_refresh_advance(clock->refresh,count*fetches);
    return (u16)count;
}
