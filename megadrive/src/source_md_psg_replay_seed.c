#include "source_md_psg_replay.h"

u8 source_md_psg_replay_seed(SourceMdPsgReplayClock *clock,u16 lines,u16 hv,u32 line_epoch)
{
    u16 h=hv&255;
    if(!clock || (lines!=262 && lines!=313) || (h>147 && h<233)) return 1;
    if(h>=233) h-=85;
    if(h<133) h+=171;
    h=(h-133)*20;
    clock->master=line_epoch+h;clock->horizontal=h;
    clock->vertical=hv&0xff00;clock->lines=lines;clock->error=0;
    return 0;
}
