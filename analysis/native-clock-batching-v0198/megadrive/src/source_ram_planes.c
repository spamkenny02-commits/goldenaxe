#include "source_ram_planes.h"
#define S(t,m) do { if(!source_clock_execute(clock,t,m,SOURCE_CLOCK_NONE,source_irq_interrupt,context)) return 0; } while(0)
u8 source_ram_planes(SourceClock *clock,SourceIrqContext *context,const u8 **source,u8 *destination,u16 address,u8 stride)
{
    u16 plane;const u8 *src=*source;
    S(4,1);
    for(plane=0;plane<stride;plane++)
    {
        u16 cursor=address+plane;u8 *write=destination+plane;
        if(!source_clock_block(clock,22,2)) {S(11,1);S(11,1);}
        for(;;)
        {
            u16 command=*src++,count,n;u8 literal;
            if(!command)
            {
                if(!source_clock_block(clock,23,3)) {S(7,1);S(4,1);S(12,1);}
                break;
            }
            literal=command&128;count=command&127;if(!count) count=256;
            if(!source_clock_block(clock,literal?39:38,6))
            {
                S(7,1);S(4,1);S(7,1);S(10,1);
                if(literal) {S(7,1);S(4,1);}else {S(4,1);S(6,1);}
            }
            for(n=0;n<count;n++)
            {
                u16 batch=0,limit,k,ticks=literal?57:51;u8 fetches=literal?8:7;
                if(stride==1 || stride==2 || stride==4)
                {
                    limit=(255-(cursor&255))>>(stride==1?0:stride==2?1:2);
                    if(!limit) {limit=1;ticks--;fetches++;}
                    else if(limit>count-n-1) limit=count-n-1;
                    if(n+1==count) {limit=1;ticks-=5;}
                    batch=source_clock_repeat(clock,ticks,fetches,limit);
                }
                if(batch)
                {
                    for(k=0;k<batch;k++) { *write=*src;write+=stride;if(literal) src++; }
                    cursor+=batch*stride;n+=batch-1;continue;
                }
                /* HL increments before each literal read in0C0D. */
                if(literal) S(6,1);
                S(7,1);S(7,1);*write=*src;write+=stride;if(literal) src++;
                S(4,1);S(4,1);S(4,1);
                if((cursor&255)+stride<256) S(12,1);
                else { S(7,1);S(4,1); }
                cursor+=stride;S(n+1<count?13:8,1);
            }
            if(!literal) src++;
            if(!source_clock_block(clock,18,2)) {S(6,1);S(12,1);}
        }
        if(!source_clock_block(clock,plane+1<stride?45:40,5))
        {S(10,1);S(10,1);S(6,1);S(6,1);S(plane+1<stride?13:8,1);}
    }
    S(10,1);*source=src;return 1;
}

#undef S
