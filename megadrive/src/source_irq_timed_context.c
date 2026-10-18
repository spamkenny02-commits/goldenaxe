#include "source_irq_timed_context.h"
#ifndef GAW_TIMED_READER
#define GAW_TIMED_READER source_audio_reader_stream_timed
#endif

#ifdef GAW_TIMED_READER_MASTER
static void discard_master(void *context,const u8 *writes,const u32 *master,u16 count)
{(void)context;(void)writes;(void)master;(void)count;}
#else
static void absolute_sink(void *context,const u8 *writes,const u32 *tstates,u16 count)
{
    SourceTimedIrqContext *ctx=(SourceTimedIrqContext *)context;
    u32 master[512];u16 n;
    if(!ctx->sink) return;
    for(n=0;n<count;n++) master[n]=ctx->reader_entry_master+tstates[n]*15;
    ctx->sink(ctx->sink_context,writes,master,count);
}
#endif
static u8 timed_audio(SourceIrqContext *core,const SourceIrqOutput *irq,SourceClockWork *work)
{
    SourceTimedIrqContext *ctx=(SourceTimedIrqContext *)core;u16 n;u32 prefix;
    /* Entry is0137 after vector/accept. Audio-only path:27T gate,203T save/
     * map and17T CALL. Full IRQ stages precede the AUDIO stage's17T CALL. */
    /* The canonical adapter commits RAM only after audio returns, so C02E
     * still selects the original IRQ path. Avoid reading the zeroed stage
     * array on audio-only calls; LTO can then remove its initialization. */
    if(core->ram[0x2e])
    {prefix=17;for(n=0;n<SOURCE_IRQ_AUDIO;n++) prefix+=irq->stages[n].tstates;}
    else prefix=247;
    ctx->reader_entry_master=core->last_entry.entry_elapsed+prefix*15;
#ifdef GAW_TIMED_READER_MASTER
    return source_audio_reader_stream_fast_master(core->audio,core->low,core->low_bytes,core->bank6,
        &core->audio_de,work,&core->last_audio,ctx->reader_entry_master,
        ctx->sink?ctx->sink:discard_master,ctx->sink_context);
#else
    return GAW_TIMED_READER(core->audio,core->low,core->low_bytes,core->bank6,
        &core->audio_de,work,&core->last_audio,absolute_sink,ctx);
#endif
}

#define GAW_SOURCE_IRQ_AUDIO(c,i,w) timed_audio(c,i,w)
#define source_irq_interrupt source_irq_timed_interrupt
#include "source_irq_context.c"
