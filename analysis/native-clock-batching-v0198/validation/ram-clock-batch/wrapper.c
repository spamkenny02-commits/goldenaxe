#include "source_ram_planes.h"
u8 source_ram_planes_scalar(SourceClock*,SourceIrqContext*,const u8**,u8*,u16,u8);
typedef struct {u32 count,data[64][5];} Log;
static void trace(void *user,const SourceClockIrq *entry,const SourceClockWork *work)
{
 Log *p=(Log*)user;u32 *r;if(p->count>=64) {p->count++;return;}
 r=p->data[p->count++];r[0]=entry->entry_elapsed;r[1]=entry->entry_raster;r[2]=entry->entry_refresh;r[3]=work->tstates;r[4]=work->fetches;
}
u8 ram_case(u8 scalar,u16 lines,u32 raster,u8 refresh,u8 iff,u8 pending,u16 address,u8 stride,
              const u8 *low,const u8 *bank,const u8 *stream,u8 *pixels,u32 *out,u32 *events,u8 *state)
{
 SourceClock clock;SourceIrqContext ctx={0};u8 ram[336]={0},audio[400]={0};Log log={0};const u8 *end=stream;u16 n,j;
 audio[3]=lines==262?0x80:0;
 if(!source_clock_init(&clock,lines,raster,refresh,iff,0,pending)) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.low_bytes=32768;ctx.bank6=bank;ctx.input.lines=lines;ctx.input.reset_mask=16;ctx.trace=trace;ctx.trace_context=&log;
 for(n=0;n<16384;n++) pixels[n]=0xa7;
 if(!(scalar?source_ram_planes_scalar(&clock,&ctx,&end,pixels,address,stride):source_ram_planes(&clock,&ctx,&end,pixels,address,stride)) || log.count>64) return 0;
 if(!source_clock_checkpoint(&clock,source_irq_interrupt,&ctx)) return 0;
 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;
 out[5]=clock.irq_tstates;out[6]=clock.irq_m1;out[7]=clock.irq_count;out[8]=clock.refresh;out[9]=clock.iff;out[10]=clock.blocked;out[11]=clock.pending;out[12]=clock.first;
 out[13]=clock.status_suppressions;out[14]=clock.vector_coalescences;out[15]=end-stream;out[16]=ctx.audio_de;out[17]=ctx.error;
 for(n=0;n<log.count;n++) for(j=0;j<5;j++) events[n*5+j]=log.data[n][j];
 for(n=0;n<336;n++) state[n]=ram[n];
 for(n=0;n<400;n++) state[336+n]=audio[n];
 return 1;
}
