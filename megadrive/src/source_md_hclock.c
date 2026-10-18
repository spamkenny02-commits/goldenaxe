#include "source_md_hclock.h"

static u8 horizontal(u16 hv,u16 *phase)
{
    u16 h=hv&255;
    if(h>147) {if(h<233) return 0;h-=85;}
    if(h<133) h+=171;
    *phase=(h-133)*20;
    return 1;
}

static u16 vertical(u16 line,u16 lines)
{
    u16 limit=lines==313?258:234;
    if(line>limit) line-=lines;
    return line&255;
}

u8 source_md_hclock_seed(SourceMdHClock *clock,u8 pal,u16 line,u16 hv,u32 origin)
{
    u16 h,lines=pal?313:262;
    u32 phase;
    if(!clock || pal>1 || line>=lines || !horizontal(hv,&h) || vertical(line,lines)!=(hv>>8))
        return SOURCE_MD_HCLOCK_INVALID;
    phase=(u32)line*3420+h;
    clock->master=origin+phase;clock->phase=phase;clock->lines=lines;
    return SOURCE_MD_HCLOCK_OK;
}

u8 source_md_hclock_sample(SourceMdHClock *clock,u16 hv)
{
    u16 h,v=hv>>8,lines,limit,candidates[3],count=0,n,matches=0;
    u32 period,bound,phase,delta,chosen=0,advance=0;
    if(!clock || (clock->lines!=262 && clock->lines!=313) || !horizontal(hv,&h))
        return SOURCE_MD_HCLOCK_INVALID;
    lines=clock->lines;period=(u32)lines*3420;limit=lines==313?258:234;
    if(clock->phase>=period) return SOURCE_MD_HCLOCK_INVALID;
    bound=(u32)(lines-256)*3420;
    if(v<=limit) candidates[count++]=v;
    if(v+256<=limit) candidates[count++]=v+256;
    if(v+lines-256>limit) candidates[count++]=v+lines-256;
    for(n=0;n<count;n++)
    {
        phase=(u32)candidates[n]*3420+h;
        delta=phase>=clock->phase?phase-clock->phase:period-clock->phase+phase;
        if(delta<bound) {matches++;chosen=phase;advance=delta;}
    }
    if(matches!=1) return SOURCE_MD_HCLOCK_GAP;
    clock->phase=chosen;clock->master+=advance;
    return SOURCE_MD_HCLOCK_OK;
}
