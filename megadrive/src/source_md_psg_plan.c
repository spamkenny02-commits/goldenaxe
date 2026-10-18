#include "source_md_psg_plan.h"

static u16 group(const SourcePsgEvent *events,u16 remaining,u16 *spacing)
{
    u32 delta;u16 limit,n=1;
    *spacing=0;
    if(remaining<2) return 1;
    delta=events[1].due-events[0].due;
    if(delta!=315 && delta!=630) return 1;
    *spacing=(u16)delta;limit=delta==315?16:8;
    while(n<remaining && n<limit && events[n].due-events[n-1].due==delta) n++;
    return n;
}

u8 source_md_psg_plan(const SourcePsgEvent *events,u16 count,SourceMdPsgBlock *blocks,u16 capacity,u16 *block_count)
{
    u16 n,needed=0,spacing,size,k;u32 first,previous;
    if(!block_count || (count && (!events || !blocks))) return SOURCE_PSG_QUEUE_INVALID;
    if(count)
    {
        first=previous=events[0].due;
        for(n=0;n<count;n++)
        {
            if((s32)(events[n].due-previous)<0 || (s32)(events[n].due-first)<0) return SOURCE_PSG_QUEUE_ORDER;
            previous=events[n].due;
        }
    }
    for(n=0;n<count;n+=size) {size=group(events+n,count-n,&spacing);needed++;}
    if(needed>capacity) return SOURCE_PSG_QUEUE_FULL;
    for(n=0,k=0;n<count;n+=size,k++)
    {
        SourceMdPsgBlock *block=blocks+k;u16 i;
        size=group(events+n,count-n,&spacing);
        block->due=events[n].due;block->count=size;block->spacing=spacing;
        block->target_hv=0x0094; /* Impossible H32 counter: no beam mapping. */
        block->skip=spacing==315?(16-size)*18:spacing==630?(8-size)*40:0;
        for(i=0;i<16;i++) block->values[i]=0;
        for(i=0;i<size;i++) block->values[16-size+i]=events[n+i].value;
    }
    *block_count=needed;return SOURCE_PSG_QUEUE_OK;
}

u8 source_md_psg_plan_beam(SourceMdPsgBlock *blocks,u16 count,u16 lines,u16 seed_line,u32 epoch)
{
    u16 n,line,h;u32 period,phase,offset;
    if((count && !blocks) || (lines!=262 && lines!=313) || seed_line>=lines) return SOURCE_PSG_QUEUE_INVALID;
    for(n=0;n<count;n++) if((s32)(blocks[n].due-epoch)<0) return SOURCE_PSG_QUEUE_ORDER;
    period=(u32)lines*3420;
    for(n=0;n<count;n++)
    {
        offset=blocks[n].due-epoch;
        phase=offset%period+(u32)seed_line*3420;
        if(phase>=period) phase-=period;
        phase=((phase+19)/20)*20;
        if(phase>=period) phase-=period;
        line=phase/3420;h=(phase%3420)/20+133;
        if(h>=171) h-=171;
        if(h>=148) h+=85;
        if(line>(lines==313?258:234)) line+=256-lines;
        blocks[n].target_hv=(line&255)*256+h;
    }
    return SOURCE_PSG_QUEUE_OK;
}
