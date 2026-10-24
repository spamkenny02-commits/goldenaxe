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

/* A separately compiled timed adapter substitutes only the reader call while
 * retaining the same IRQ staging, diagnostics and clock-work publication. */
#ifndef GAW_SOURCE_IRQ_AUDIO
static void ignore(void *context,const u8 *writes,u16 count)
{(void)context;(void)writes;(void)count;}
#define GAW_SOURCE_IRQ_AUDIO(c,i,w) source_audio_reader_stream_fast((c)->audio,(c)->low,(c)->low_bytes,(c)->bank6,&(c)->audio_de,w,&(c)->last_audio,(c)->sink?(c)->sink:ignore,(c)->sink_context)
#endif

u8 source_irq_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work)
{
    SourceIrqContext *ctx=(SourceIrqContext *)context;
    u8 ram[336],full,timer_after=0;SourceIrqInput input;SourceIrqOutput irq;
    SourceClockWork zero={0,0},audio;u32 period,start,ack,until;
    work->tstates=work->fetches=0;ctx->error=0;ctx->last_entry=*entry;
    full=ctx->ram[0x2e]!=0;input=ctx->input;
    input.raster=entry->entry_raster;input.compensation=ctx->audio[3];
    if(full)
    {
        if(ctx->video && !ctx->video(ctx->video_context,ctx,entry,&input.tile_count))
        {ctx->error=SOURCE_IRQ_CONTEXT_VIDEO;return 0;}
        copy_state(ram,ctx->ram);
        if(!source_irq(ram,&input,&zero,&irq)) {ctx->error=SOURCE_IRQ_CONTEXT_INVALID;return 0;}
    }
    else
    {
        /* The source audio-only IRQ changes just C030. Stage that byte,
         * rather than copying all336 RAM bytes into and out of a buffer. */
        u8 timer_before=ctx->ram[0x30];
        if(!source_irq(ctx->ram,&input,&zero,&irq)) {ctx->error=SOURCE_IRQ_CONTEXT_INVALID;return 0;}
        timer_after=ctx->ram[0x30];ctx->ram[0x30]=timer_before;
    }
    if(!GAW_SOURCE_IRQ_AUDIO(ctx,&irq,&audio))
    {ctx->error=ctx->last_audio.error;return 0;}
    if(audio.tstates>0xffffffffUL-irq.whole.tstates || audio.fetches>0xffffffffUL-irq.whole.fetches)
    {ctx->error=SOURCE_IRQ_CONTEXT_INVALID;return 0;}
    irq.whole.tstates+=audio.tstates;irq.whole.fetches+=audio.fetches;
    if(full)
    {
        irq.stages[SOURCE_IRQ_AUDIO].tstates+=audio.tstates;
        irq.stages[SOURCE_IRQ_AUDIO].fetches+=audio.fetches;
    }
    if(full) ctx->last_irq=irq;
    else
    {
        /* All audio-only stage fields are zero. Avoid reading/copying the
         * complete temporary stage array just to publish those zeros. */
#ifdef SGDK_GCC
        memset(&ctx->last_irq,0,sizeof(ctx->last_irq));
#else
        __builtin_memset(&ctx->last_irq,0,sizeof(ctx->last_irq));
#endif
        ctx->last_irq.whole=irq.whole;
    }
    if(irq.reset_requested)
    {if(full) copy_state(ctx->ram,ram);else ctx->ram[0x30]=timer_after;ctx->error=SOURCE_IRQ_CONTEXT_RESET;return 0;}
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
    if(full) copy_state(ctx->ram,ram);else ctx->ram[0x30]=timer_after;
    *work=irq.whole;
    if(ctx->trace) ctx->trace(ctx->trace_context,entry,work);
    return 1;
}
