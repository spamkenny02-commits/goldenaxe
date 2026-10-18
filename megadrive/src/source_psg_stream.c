#include "source_psg_stream.h"

u8 source_psg_stream_init(SourcePsgStream *stream,SourcePsgQueue *queue,SourcePsgPump pump,void *context)
{
    if(!stream || !pump || source_psg_queue_push_bytes(queue,0,0,0)!=SOURCE_PSG_QUEUE_OK ||
       queue->read!=queue->write) return SOURCE_PSG_QUEUE_INVALID;
    stream->queue=queue;stream->pump=pump;stream->context=context;
    stream->error=0;stream->published=stream->waits=0;return SOURCE_PSG_QUEUE_OK;
}

void source_psg_stream_sink(void *context,const u8 *values,const u32 *due,u16 count)
{
    SourcePsgStream *stream=(SourcePsgStream *)context;u8 status;
    if(!stream || stream->error) return;
    if(count>512 || !stream->queue || !stream->pump)
    {stream->error=SOURCE_PSG_QUEUE_INVALID;return;}
    for(;;)
    {
        status=source_psg_queue_push_bytes(stream->queue,values,due,count);
        if(status==SOURCE_PSG_QUEUE_OK) {stream->published+=count;return;}
        if(status!=SOURCE_PSG_QUEUE_FULL || count>stream->queue->capacity)
        {stream->error=status;return;}
        stream->waits++;
        if(!stream->pump(stream->context)) {stream->error=SOURCE_PSG_STREAM_CANCELLED;return;}
        if(stream->error) return;
    }
}
