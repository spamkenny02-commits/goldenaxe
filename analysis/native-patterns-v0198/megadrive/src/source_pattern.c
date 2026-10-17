#include "source_pattern.h"

const u8 *source_pattern_decode(const u8 *source,u8 *destination,u16 address,
                                SourceClockWork *work)
{
    u16 plane,last=address;
    /* Keep optional accounting out of the production inner loop. */
    if(!work)
    {
        for(plane=0;plane<4;plane++)
        {
            u8 *write=destination+plane;u16 command;
            while((command=*source++)!=0)
            {
                u16 count=command&127;
                if(!count) count=256;
                while(count--)
                {
                    *write=*source;write+=4;
                    if(command&128) source++;
                }
                if(!(command&128)) source++;
            }
        }
        return source;
    }
    if(work) { work->tstates=11;work->fetches=2; }
    for(plane=0;plane<4;plane++)
    {
        u8 *write=destination+plane;
        u16 cursor=address+plane,command;
        if(work) { work->tstates+=22;work->fetches+=2; }
        for(;;)
        {
            command=*source++;
            if(work) { work->tstates+=17;work->fetches+=3; }
            if(!command)
            {
                if(work) { work->tstates+=12;work->fetches++; }
                break;
            }
            {
                u16 count=command&127,n;
                u8 literal=command&128;
                if(!count) count=256; /* DJNZ with B=0. */
                if(work) { work->tstates+=27;work->fetches+=6; }
                for(n=0;n<count;n++)
                {
                    *write=*source;write+=4;
                    if(literal) source++;
                    if(work)
                    {
                        /* RST28 (including DI/EI), OUT and source/dest steps. */
                        work->tstates+=59+7+11+4+(literal?13:12)+16;
                        work->fetches+=16+(literal?1:0);
                        if((cursor&255)<252) { work->tstates+=12;work->fetches++; }
                        else { work->tstates+=11;work->fetches+=2; }
                        work->tstates+=(n+1<count)?13:8;work->fetches++;
                    }
                    cursor+=4;
                }
                if(!literal) source++;
                if(work)
                {
                    work->tstates+=literal?16:29;
                    work->fetches+=literal?2:4;
                }
            }
        }
        last=cursor;
        if(work) { work->tstates+=46+(plane<3?13:8);work->fetches+=5; }
    }
    if(work)
    {
        work->tstates+=48+(((last+1)&255)>=4?12:11);
        work->fetches+=(((last+1)&255)>=4)?7:8;
    }
    return source;
}
