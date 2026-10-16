#include "source_clock.h"
typedef struct { u32 tstates,fetches,elapsed_sum,raster_sum,refresh_sum; } TestInterrupt;
static u8 test_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work)
{ TestInterrupt *p=context;p->elapsed_sum+=entry->entry_elapsed;p->raster_sum+=entry->entry_raster;p->refresh_sum+=entry->entry_refresh;work->tstates=p->tstates;work->fetches=p->fetches;return 1; }
u8 clock_case(const u32 *input,const u16 *plan,u16 length,u32 *out)
{
 SourceClock clock;TestInterrupt context={0};u16 i;
 context.tstates=input[6];context.fetches=input[7];
 if(!source_clock_init(&clock,input[0],input[1],input[2],input[3],input[4],input[5])) return 0;
 for(i=0;i<length;i++) if(!source_clock_execute(&clock,plan[i*3],plan[i*3+1],plan[i*3+2],test_interrupt,&context)) return 0;
 if(!source_clock_checkpoint(&clock,test_interrupt,&context)) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;
 out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;out[5]=clock.irq_tstates;out[6]=clock.irq_m1;
 out[7]=clock.refresh;out[8]=clock.iff;out[9]=clock.blocked;out[10]=clock.pending;out[11]=clock.first;
 out[12]=clock.status_suppressions;out[13]=clock.vector_coalescences;out[14]=clock.irq_count;
 out[15]=context.elapsed_sum;out[16]=context.raster_sum;out[17]=context.refresh_sum;return 1;
}
