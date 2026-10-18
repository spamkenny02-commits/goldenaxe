#ifndef GAW_SOURCE_IRQ_QUEUE_CONTEXT_H
#define GAW_SOURCE_IRQ_QUEUE_CONTEXT_H
#include "source_irq_timed_context.h"
#include "source_psg_stream.h"
typedef struct {
    SourceTimedIrqContext timed; /* core remains the first nested member. */
    SourcePsgStream stream;
} SourceQueuedIrqContext;
enum {SOURCE_IRQ_CONTEXT_QUEUE=0x900};
/* Bind before running the loader, with consumer stopped and queue empty.
 * Capacity>=512 accommodates any bounded reader packet without staging RAM.
 * Existing core fields and trace stay unchanged; setup failure is atomic. */
u8 source_irq_queue_bind(SourceQueuedIrqContext *context,SourcePsgQueue *queue,SourcePsgPump pump,void *user);
/* Fast timed IRQ semantics with complete-packet FIFO publication. Fatal
 * stream faults invalidate work before IRQ RAM/trace commit. Earlier audio
 * state/packets can remain, as with other fast-stream failures: reset session,
 * never retry that IRQ. last_audio.count reports actually published bytes.
 * Backpressure does not add fabricated source work or physical pacing. */
u8 source_irq_queue_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
#endif
