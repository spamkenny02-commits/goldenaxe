#ifndef GAW_SOURCE_PSG_STREAM_H
#define GAW_SOURCE_PSG_STREAM_H
#include "source_psg_queue.h"

/* Called only when an entire packet cannot fit. May advance/wait for the
 * consumer; must not reenter the producer, reset the stream or publish.
 * Return0 to cancel the session,1 to retry. No physical clock is supplied. */
typedef u8 (*SourcePsgPump)(void *context);
typedef struct {
    SourcePsgQueue *queue;
    SourcePsgPump pump;
    void *context;
    volatile u16 error;
    u32 published,waits;
} SourcePsgStream;
enum {SOURCE_PSG_STREAM_CANCELLED=0x100};

/* Initialize with consumer stopped and queue empty. Invalid setup leaves
 * the stream untouched. Queue/status codes are shared with source_psg_queue.
 * Stream/queue/input storage must not overlap. One producer on one68000. */
u8 source_psg_stream_init(SourcePsgStream *stream,SourcePsgQueue *queue,SourcePsgPump pump,void *context);
/* SourceIrqTimedSink-compatible callback. Packets contain at most512 bytes.
 * FULL retries the same complete packet; no prefix is exposed. Other faults
 * latch error and fence subsequent callbacks. A fatal session cannot retry
 * its IRQ: reader state may have advanced and prior packets were published.
 * Stop/reset producer and consumer to recover. Consumer must observe error.
 * Queue availability does NOT establish physical deadline compliance. */
void source_psg_stream_sink(void *context,const u8 *values,const u32 *due,u16 count);
#endif
