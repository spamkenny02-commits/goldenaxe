#include "source_pattern_clock.h"

/* Detailed instruction boundaries are retained near interrupts. Interior
 * bytes may batch only before VINT with IFF/EI-delay restored at byte end. */
static u8 step(SourceClock *clock,SourceIrqContext *context,u16 ticks,u8 fetches,u8 effect)
{
    if(effect==SOURCE_CLOCK_NONE && source_clock_block(clock,ticks,fetches)) return 1;
    return source_clock_execute(clock,ticks,fetches,effect,source_irq_interrupt,context);
}
#define S(t,m) do { if(!step(clock,context,t,m,SOURCE_CLOCK_NONE)) return 0; } while(0)
static u8 rst28(SourceClock *clock,SourceIrqContext *context)
{
    S(11,1);
    if(!step(clock,context,4,1,SOURCE_CLOCK_DI)) return 0;
    S(4,1);S(11,1);S(4,1);S(11,1);
    if(!step(clock,context,4,1,SOURCE_CLOCK_EI)) return 0;
    S(10,1);return 1;
}

/* ROM input is immutable. Scan complete commands up to the next VINT,
 * then commit their decoded bytes before the next clock operation. No
 * plane-end RAM write is included in this window. */
static u16 command_window(SourceClock *clock,const u8 **source,u8 **destination,u16 *cursor)
{
    const u8 *scan=*source,*src;u8 *write;
    u32 available;u16 ticks=0,fetches=0,commands=0,position=*cursor;
    if(clock->first || clock->blocked || clock->pending || !clock->iff) return 0;
    available=clock->until_vint/15;
    if(available>65535) available=65535;
    while(*scan)
    {
        u16 command=*scan,count=command&127,carry,cost,m1;u8 literal=command&128;
        if(!count) count=256;
        carry=((position&255)+count*4)>>8;
        cost=44+count*(literal?135:134)-carry-5+(literal?16:29);
        m1=9+count*(literal?19:18)+carry+(literal?2:4);
        if(cost>available-ticks) break;
        ticks+=cost;fetches+=m1;position+=count*4;commands++;
        scan+=1+(literal?count:1);
    }
    if(commands<2 || !source_clock_block(clock,ticks,fetches)) return 0;
    src=*source;write=*destination;
    while(src<scan)
    {
        u16 command=*src++,count=command&127,n;u8 literal=command&128;
        if(!count) count=256;
        for(n=0;n<count;n++) {*write=*src;write+=4;if(literal) src++;}
        if(!literal) src++;
    }
    *source=scan;*destination=write;*cursor=position;
    return commands;
}

static u16 planned_window(SourceClock *clock,const SourcePatternPlane *plan,u16 *index,
                          const u8 **source,u8 **destination,u16 *cursor)
{
    const SourcePatternBoundary *base,*end;u32 available;u16 lo=*index,hi=plan->count,mid,n;
    u8 *write=*destination;
    if(lo>=hi || clock->first || clock->blocked || clock->pending || !clock->iff) return 0;
    available=clock->until_vint/15;if(available>65535) available=65535;
    base=plan->boundary+lo;
    while(lo<hi)
    {
        mid=lo+((hi-lo+1)>>1);
        if(plan->boundary[mid].ticks-base->ticks<=available) lo=mid;else hi=mid-1;
    }
    if(lo==*index) return 0;
    end=plan->boundary+lo;
    if(!source_clock_block(clock,(u16)(end->ticks-base->ticks),(u16)(end->fetches-base->fetches))) return 0;
    for(n=base->decoded;n<end->decoded;n++) {*write=plan->decoded[n];write+=4;}
    *source+=end->source-base->source;*destination=write;
    *cursor+=(end->decoded-base->decoded)*4;*index=lo;
    return 1;
}

static u8 patterns032a(SourceClock *clock,SourceIrqContext *context,
                       const u8 **source,u8 *destination,const SourcePatternPlan *plan)
{
    u16 plane,cursor=0x4000;
    const u8 *src=*source;
    if(!source_clock_block(clock,11,2)) {S(7,1);S(4,1);}
    for(plane=0;plane<4;plane++)
    {
        u8 *write=destination+plane;u16 command_index=0;
        cursor=0x4000+plane;
        if(!source_clock_block(clock,22,2)) {S(11,1);S(11,1);}
        for(;;)
        {
            u16 command,count,n;
            u8 literal;
            if(plan)
            {if(planned_window(clock,plan->planes+plane,&command_index,&src,&write,&cursor)) continue;}
            else if(command_window(clock,&src,&write,&cursor)) continue;
            command=*src++;
            if(!command)
            {
                if(!source_clock_block(clock,29,4)) {S(7,1);S(6,1);S(4,1);S(12,1);}
                break;
            }
            literal=command&128;count=command&127;if(!count) count=256;
            if(plan) command_index++;
            /* A complete RLE command has no observable intermediate state
             * if it fits before VINT. Include every page carry and the
             * final short DJNZ; fall back to byte/instruction boundaries. */
            {
                u16 carries=((cursor&255)+count*4)>>8;
                u16 ticks=44+count*(literal?135:134)-carries-5+(literal?16:29);
                u16 fetches=9+count*(literal?19:18)+carries+(literal?2:4);
                if(source_clock_block(clock,ticks,fetches))
                {
                    for(n=0;n<count;n++) { *write=*src;write+=4;if(literal) src++; }
                    if(!literal) src++;
                    cursor+=count*4;continue;
                }
            }
            if(!source_clock_block(clock,44,9))
            {S(7,1);S(6,1);S(4,1);S(7,1);S(4,1);S(8,2);S(4,1);S(4,1);}
            for(n=0;n<count;n++)
            {
                u16 limit,batch,k,ticks=literal?135:134;u8 fetches=literal?19:18;
                /* A regular byte is135T/19M1 literal,134T/18M1 repeat.
                 * Carry costs one fewer T/one more M1; terminal DJNZ saves5T.
                 * RST28's DI/EI delay has expired at every byte boundary. */
                limit=(255-(cursor&255))>>2;
                if(!limit) {limit=1;ticks--;fetches++;}
                else if(limit>count-n-1) limit=count-n-1;
                if(n+1==count) {limit=1;ticks-=5;}
                batch=source_clock_repeat(clock,ticks,fetches,limit);
                if(batch)
                {
                    for(k=0;k<batch;k++) { *write=*src;write+=4;if(literal) src++; }
                    cursor+=batch*4;n+=batch-1;continue;
                }
                if(!rst28(clock,context)) return 0;
                S(7,1);S(11,1);S(4,1);S(literal?7:12,1);
                *write=*src;write+=4;
                if(literal) { S(6,1);src++; }
                S(4,1);S(4,1);S(4,1);S(4,1);
                if((cursor&255)<252) S(12,1);
                else { S(7,1);S(4,1); }
                cursor+=4;S(n+1<count?13:8,1);
            }
            if(!source_clock_block(clock,literal?16:29,literal?2:4))
            {
                S(4,1);
                if(literal) S(12,1);else {S(7,1);S(6,1);S(12,1);}
            }
            if(!literal) src++;
        }
        if(source_clock_block(clock,plane<3?59:54,6))
        {context->ram[0x31]=cursor;context->ram[0x32]=cursor>>8;}
        else
        {
            S(20,2);context->ram[0x31]=cursor;context->ram[0x32]=cursor>>8;
            S(10,1);S(6,1);S(10,1);S(plane<3?13:8,1);
        }
    }
    if(!source_clock_block(clock,((cursor+1)&255)>=4?60:59,((cursor+1)&255)>=4?8:9))
    {
        S(20,2);S(6,1);S(4,1);S(4,1);S(4,1);
        if(((cursor+1)&255)>=4) S(12,1);else {S(7,1);S(4,1);}
        S(10,1);
    }
    *source=src;return 1;
}

u8 source_graphics_prefix_changed(SourceClock *clock,SourceIrqContext *context,u16 room,
                                 const u8 *patterns,u8 *destination,const u8 **end,const SourcePatternPlan *plan)
{
    static const u8 palette[]={10,7,7,10,7,7,5,7,13,13};
    static const u8 before_copy[]={13,7,10,13,13,10,10,10};
    u16 n;u8 graphics;
    if(!clock || !context || !context->ram || !context->audio || !patterns ||
       !destination || !end || context->ram[0x2e] || (context->ram[0x11]&64) ||
       clock->period!=(u32)context->input.lines*3420) return 0;
    /* 175F: high room byte selects dungeons, then low<10 or low nibbleF
     * selects houses. Preserve the different taken-branch T/M1 costs. */
    S(17,1);S(13,1);S(4,1);S(7,1);
    if(room>>8) {S(12,1);graphics=2;}
    else
    {
        S(7,1);S(13,1);S(7,1);S(7,1);
        if((room&255)<16) {S(12,1);graphics=1;}
        else
        {
            S(7,1);S(13,1);S(7,1);S(7,1);S(7,1);
            if((room&15)==15) {S(12,1);graphics=1;}
            else {S(7,1);S(4,1);graphics=0;}
        }
    }
    S(13,1);context->ram[0x40]=graphics;S(10,1);
    for(n=0;n<sizeof(palette);n++) S(palette[n],1);
    context->audio[6]=0xb0;
    for(n=0;n<sizeof(before_copy);n++) S(before_copy[n],1);
    for(n=0;n<15;n++) S(21,2);
    S(16,2);S(10,1);S(17,1);
    if(!patterns032a(clock,context,&patterns,destination,plan)) return 0;
    *end=patterns;
    return source_clock_checkpoint(clock,source_irq_interrupt,context);
}
u8 source_graphics_prefix_class0_planned(SourceClock *clock,SourceIrqContext *context,
                                 const u8 *patterns,u8 *destination,const u8 **end,const SourcePatternPlan *plan)
{return source_graphics_prefix_changed(clock,context,0x10,patterns,destination,end,plan);}
u8 source_graphics_prefix_class0(SourceClock *clock,SourceIrqContext *context,
                                 const u8 *patterns,u8 *destination,const u8 **end)
{return source_graphics_prefix_class0_planned(clock,context,patterns,destination,end,0);}
#undef S
