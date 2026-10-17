#include "../../../megadrive/src/source_pattern_clock.h"
extern u8 shared_pixels[16384];
#include "../../../megadrive/src/source_pattern_plan_generated.h"
typedef struct {u32 count,events[64][6];SourceIrqContext *irq;} WaitTrace;
static void trace(void *context,const SourceClockIrq *entry,const SourceClockWork *work)
{
 WaitTrace *p=(WaitTrace *)context;u32 *row;
 if(p->count>=64) {p->count++;return;}
 row=p->events[p->count++];row[0]=entry->entry_elapsed;row[1]=entry->entry_raster;
 row[2]=entry->entry_refresh;row[3]=work->tstates;row[4]=work->fetches;
 row[5]=p->irq->last_irq.stages[SOURCE_IRQ_SAT64].tstates!=0;
}
u8 prefix_fast_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,
              const u8 *bank6,const u8 *patterns,u16 tile_count,u32 *out,u32 *events,u8 *pixel_output)
{
 SourceClock clock;SourceIrqContext ctx={0};const u8 *end;u8 *pixels=shared_pixels;WaitTrace log={0};
 s32 raster=(s32)(phase[1]*3420)+(s32)(phase[0]-phase[2]);u32 period=phase[3]*3420;u16 n,j;
 if((phase[3]!=262 && phase[3]!=313) || phase[5] || (phase[6]&4) || !(phase[6]&32) ||
    (phase[7]!=32 && phase[7]!=33) || (phase[11]&16)) return 0;
 while(raster<0) raster+=period;
 while((u32)raster>=period) raster-=period;
 if(!source_clock_init(&clock,phase[3],raster,refresh,phase[8],phase[9],phase[10])) return 0;
 ctx.ram=ram;ctx.audio=audio;ctx.low=low;ctx.bank6=bank6;ctx.low_bytes=32768;
 ctx.input.lines=phase[3];ctx.input.tile_count=tile_count;ctx.input.reset_mask=16;
 ctx.trace=trace;ctx.trace_context=&log;log.irq=&ctx;
 for(n=0;n<16384;n++) pixels[n]=0xa7;
 if(!source_graphics_prefix_class0_planned(&clock,&ctx,patterns,pixels,&end,&gaw_class0_pattern_plan) || log.count>64) return 0;

 out[0]=clock.raster;out[1]=clock.until_vint;out[2]=clock.elapsed;
 out[3]=clock.foreground_tstates;out[4]=clock.foreground_m1;out[5]=clock.irq_tstates;out[6]=clock.irq_m1;
 out[7]=clock.irq_count;out[8]=clock.status_suppressions;out[9]=clock.vector_coalescences;
 out[10]=clock.refresh;out[11]=clock.iff;out[12]=clock.blocked;out[13]=clock.pending;out[14]=clock.first;
 out[15]=end-patterns;out[18]=0;out[19]=0;out[16]=ctx.error;out[17]=ctx.audio_de;
 for(n=0;n<log.count;n++) for(j=0;j<6;j++) events[n*6+j]=log.events[n][j];
 for(n=0;n<16384;n++) pixel_output[n]=pixels[n];
 return 1;
}
