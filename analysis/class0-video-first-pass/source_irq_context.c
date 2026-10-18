#include "source_irq_context.h"
#include "source_audio_fast.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif

static void copy_state(u8 *to,const u8 *from)
{
#ifdef SGDK_GCC
    memcpy(to,from,336);
#else
    __builtin_memcpy(to,from,336);
#endif
}

static void ignore(void *context,const u8 *writes,u16 count)
{(void)context;(void)writes;(void)count;}

u8 source_irq_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work)
{
    SourceIrqContext *ctx=(SourceIrqContext *)context;
    u8 ram[336],full;SourceIrqInput input;SourceIrqOutput irq;
    SourceClockWork zero={0,0},audio;u32 period,start,ack,until;
    work->tstates=work->fetches=0;ctx->error=0;ctx->last_entry=*entry;
    copy_state(ram,ctx->ram);full=ram[0x2e]!=0;input=ctx->input;
    input.raster=entry->entry_raster;input.compensation=ctx->audio[3];
    if(!source_irq(ram,&input,&zero,&irq)) {ctx->error=SOURCE_IRQ_CONTEXT_INVALID;return 0;}
    if(!source_audio_reader_stream_fast(ctx->audio,ctx->low,ctx->low_bytes,ctx->bank6,
                                   &ctx->audio_de,&audio,&ctx->last_audio,
                                   ctx->sink?ctx->sink:ignore,ctx->sink_context))
    {ctx->error=ctx->last_audio.error;return 0;}
    if(audio.tstates>0xffffffffUL-irq.whole.tstates || audio.fetches>0xffffffffUL-irq.whole.fetches)
    {ctx->error=SOURCE_IRQ_CONTEXT_INVALID;return 0;}
    irq.whole.tstates+=audio.tstates;irq.whole.fetches+=audio.fetches;
    if(full)
    {
        irq.stages[SOURCE_IRQ_AUDIO].tstates+=audio.tstates;
        irq.stages[SOURCE_IRQ_AUDIO].fetches+=audio.fetches;
    }
    ctx->last_irq=irq;
    if(irq.reset_requested)
    {copy_state(ctx->ram,ram);ctx->error=SOURCE_IRQ_CONTEXT_RESET;return 0;}
    if(full)
    {
        period=(u32)input.lines*3420;
        start=entry->entry_raster>=72UL*15?entry->entry_raster-72UL*15:
                                               entry->entry_raster+period-72UL*15;
        ack=start+35UL*15;if(ack>=period) ack-=period;
        until=ack<193UL*3420?193UL*3420-ack:period-(ack-193UL*3420);
        if(irq.whole.tstates>0xffffffffUL/15 || (irq.whole.tstates-35)*15>=until)
        {ctx->error=SOURCE_IRQ_CONTEXT_NESTED;return 0;}
    }
    copy_state(ctx->ram,ram);*work=irq.whole;
    if(ctx->trace) ctx->trace(ctx->trace_context,entry,work);
    return 1;
}
