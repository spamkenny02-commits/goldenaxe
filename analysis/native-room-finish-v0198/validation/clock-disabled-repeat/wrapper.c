#include "source_clock.h"
static void dump(const SourceClock *p,u32 *o)
{
 o[0]=p->period;o[1]=p->raster;o[2]=p->until_vint;o[3]=p->elapsed;
 o[4]=p->foreground_tstates;o[5]=p->foreground_m1;o[6]=p->irq_tstates;o[7]=p->irq_m1;
 o[8]=p->irq_count;o[9]=p->status_suppressions;o[10]=p->vector_coalescences;
 o[11]=p->refresh;o[12]=p->iff;o[13]=p->blocked;o[14]=p->pending;o[15]=p->first;
}
u8 disabled_case(u16 lines,u32 raster,u8 refresh,u8 pending,u16 count,u32 *out)
{
 SourceClock fast,slow;u16 n;
 if(!source_clock_init(&fast,lines,raster,refresh,0,0,pending)) return 0;
 if(!source_clock_execute(&fast,4,1,SOURCE_CLOCK_NONE,0,0)) return 0;
 slow=fast;
 if(source_clock_repeat_disabled(&fast,29,3,count)!=count) return 0;
 for(n=0;n<count;n++)
  if(!source_clock_execute(&slow,16,2,SOURCE_CLOCK_NONE,0,0) || !source_clock_execute(&slow,13,1,SOURCE_CLOCK_NONE,0,0)) return 0;
 dump(&fast,out);dump(&slow,out+16);return 1;
}
u8 disabled_guard(u8 first,u8 blocked,u8 enabled,u16 ticks,u8 m1,u16 count,u32 *out)
{
 SourceClock clock;u16 accepted;
 source_clock_init(&clock,262,100,127,enabled,blocked,1);clock.first=first;
 dump(&clock,out);accepted=source_clock_repeat_disabled(&clock,ticks,m1,count);dump(&clock,out+16);
 return accepted!=0;
}
