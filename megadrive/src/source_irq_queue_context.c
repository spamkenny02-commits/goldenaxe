#include "source_irq_queue_context.h"

u8 source_irq_queue_bind(SourceQueuedIrqContext *context,SourcePsgQueue *queue,SourcePsgPump pump,void *user)
{
    u8 result;
    if(!context || !queue || queue->capacity<512) return SOURCE_PSG_QUEUE_INVALID;
    result=source_psg_stream_init(&context->stream,queue,pump,user);
    if(result!=SOURCE_PSG_QUEUE_OK) return result;
    context->timed.sink=source_psg_stream_sink;context->timed.sink_context=&context->stream;
    return SOURCE_PSG_QUEUE_OK;
}

static u8 queued_reader(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,u16 *de,
                       SourceClockWork *work,SourceAudioReaderStatus *status,SourceAudioTimedReaderSink sink,void *context)
{
    SourceQueuedIrqContext *queued=(SourceQueuedIrqContext *)context;
    u8 accepted;u32 before=queued->stream.published;
    if(!queued->stream.queue || !queued->stream.pump)
        queued->stream.error=SOURCE_PSG_QUEUE_INVALID;
    if(queued->stream.error)
    {
        work->tstates=work->fetches=0;status->count=status->track=0;
        status->error=SOURCE_IRQ_CONTEXT_QUEUE;return 0;
    }
    accepted=source_audio_reader_stream_fast_timed(state,low,low_bytes,bank,de,work,status,sink,context);
    if(queued->stream.error)
    {
        work->tstates=work->fetches=0;status->count=(u16)(queued->stream.published-before);
        status->error=SOURCE_IRQ_CONTEXT_QUEUE;return 0;
    }
    return accepted;
}

#define GAW_TIMED_READER queued_reader
#define source_irq_timed_interrupt source_irq_queue_interrupt
#include "source_irq_timed_context.c"
