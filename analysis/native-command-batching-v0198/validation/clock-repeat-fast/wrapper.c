#include "source_clock.h"
#include "source_rng.h"
u16 reference_clock_repeat(SourceClock*,u16,u8,u16);
u8 reference_clock_execute(SourceClock*,u16,u8,u8,SourceClockInterrupt,void*);
static void dump(const SourceClock *p,u32 *o)
{
 o[0]=p->period;o[1]=p->raster;o[2]=p->until_vint;o[3]=p->elapsed;
 o[4]=p->foreground_tstates;o[5]=p->foreground_m1;o[6]=p->irq_tstates;o[7]=p->irq_m1;
 o[8]=p->irq_count;o[9]=p->status_suppressions;o[10]=p->vector_coalescences;
 o[11]=p->refresh;o[12]=p->iff;o[13]=p->blocked;o[14]=p->pending;o[15]=p->first;
}
u8 repeat_pair(u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,u8 blocked,u8 first,u16 ticks,u16 m1,u16 reps,u32 *out)
{
 SourceClock a,b;
 if(!source_clock_init(&a,lines,raster,refresh,iff,blocked,pending)) return 0;
 a.first=first;a.elapsed=a.foreground_tstates=a.foreground_m1=0xffffff00UL;b=a;
 if(reps==65534) {out[0]=source_clock_plain(&a,ticks,(u8)m1,0,0);out[1]=reference_clock_execute(&b,ticks,(u8)m1,SOURCE_CLOCK_NONE,0,0);}
 else {out[0]=reps==1?source_clock_block(&a,ticks,m1):source_clock_repeat(&a,ticks,m1,reps);out[1]=reference_clock_repeat(&b,ticks,(reps==1 && m1)?1:(u8)m1,reps);}
 if(reps==1 && out[1]) {b.foreground_m1+=m1-1;b.refresh=source_refresh_advance(b.refresh,m1-1);}
 dump(&a,out+2);dump(&b,out+18);return 1;
}
