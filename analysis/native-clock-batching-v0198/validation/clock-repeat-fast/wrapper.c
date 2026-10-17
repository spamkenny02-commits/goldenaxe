#include "source_clock.h"
u16 reference_clock_repeat(SourceClock*,u16,u8,u16);
static void dump(const SourceClock *p,u32 *o)
{
 o[0]=p->period;o[1]=p->raster;o[2]=p->until_vint;o[3]=p->elapsed;
 o[4]=p->foreground_tstates;o[5]=p->foreground_m1;o[6]=p->irq_tstates;o[7]=p->irq_m1;
 o[8]=p->irq_count;o[9]=p->status_suppressions;o[10]=p->vector_coalescences;
 o[11]=p->refresh;o[12]=p->iff;o[13]=p->blocked;o[14]=p->pending;o[15]=p->first;
}
u8 repeat_pair(u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,u8 blocked,u8 first,u16 ticks,u8 m1,u16 reps,u32 *out)
{
 SourceClock a,b;
 if(!source_clock_init(&a,lines,raster,refresh,iff,blocked,pending)) return 0;
 a.first=first;a.elapsed=a.foreground_tstates=a.foreground_m1=0xffffff00UL;b=a;
 out[0]=reps==1?source_clock_block(&a,ticks,m1):source_clock_repeat(&a,ticks,m1,reps);out[1]=reference_clock_repeat(&b,ticks,m1,reps);
 dump(&a,out+2);dump(&b,out+18);return 1;
}
