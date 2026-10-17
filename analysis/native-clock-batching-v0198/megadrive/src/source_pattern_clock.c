#include "source_pattern_clock.h"

/* Detailed instruction boundaries are retained near interrupts. Interior
 * bytes may batch only before VINT with IFF/EI-delay restored at byte end. */
static u8 step(SourceClock *clock,SourceIrqContext *context,u16 ticks,u8 fetches,u8 effect)
{
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

static u8 patterns032a(SourceClock *clock,SourceIrqContext *context,
                       const u8 **source,u8 *destination)
{
    u16 plane,cursor=0x4000;
    const u8 *src=*source;
    if(!source_clock_block(clock,11,2)) {S(7,1);S(4,1);}
    for(plane=0;plane<4;plane++)
    {
        u8 *write=destination+plane;
        cursor=0x4000+plane;
        if(!source_clock_block(clock,22,2)) {S(11,1);S(11,1);}
        for(;;)
        {
            u16 command=*src++,count,n;
            u8 literal;
            if(!command)
            {
                if(!source_clock_block(clock,29,4)) {S(7,1);S(6,1);S(4,1);S(12,1);}
                break;
            }
            if(!source_clock_block(clock,44,9))
            {S(7,1);S(6,1);S(4,1);S(7,1);S(4,1);S(8,2);S(4,1);S(4,1);}
            literal=command&128;count=command&127;if(!count) count=256;
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

u8 source_graphics_prefix_class0(SourceClock *clock,SourceIrqContext *context,
                                 const u8 *patterns,u8 *destination,const u8 **end)
{
    static const u8 classify[]={17,13,4,7,7,13,7,7,7,13,7,7,7,7,4,13};
    static const u8 palette[]={10,7,7,10,7,7,5,7,13,13};
    static const u8 before_copy[]={13,7,10,13,13,10,10,10};
    u16 n;
    if(!clock || !context || !context->ram || !context->audio || !patterns ||
       !destination || !end || context->ram[0x2e] || (context->ram[0x11]&64) ||
       clock->period!=(u32)context->input.lines*3420) return 0;
    for(n=0;n<sizeof(classify);n++) S(classify[n],1);
    context->ram[0x40]=0;S(10,1);
    for(n=0;n<sizeof(palette);n++) S(palette[n],1);
    context->audio[6]=0xb0;
    for(n=0;n<sizeof(before_copy);n++) S(before_copy[n],1);
    for(n=0;n<15;n++) S(21,2);
    S(16,2);S(10,1);S(17,1);
    if(!patterns032a(clock,context,&patterns,destination)) return 0;
    *end=patterns;
    return source_clock_checkpoint(clock,source_irq_interrupt,context);
}
#undef S
