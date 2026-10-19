#ifndef GAW_SOURCE_PSG_QUEUE_H
#define GAW_SOURCE_PSG_QUEUE_H
#include <types.h>

typedef struct {u32 due;u8 value;} SourcePsgEvent;
typedef struct {
    SourcePsgEvent *events;
    u16 capacity,mask;
    volatile u16 read,write;
} SourcePsgQueue;
enum {
    SOURCE_PSG_QUEUE_OK,SOURCE_PSG_QUEUE_INVALID,SOURCE_PSG_QUEUE_FULL,
    SOURCE_PSG_QUEUE_ORDER,SOURCE_PSG_QUEUE_WAIT,SOURCE_PSG_QUEUE_EMPTY
};

/* Caller-owned storage, power-of-two capacity1..32768. Initialize while the
 * consumer is stopped; invalid initialization leaves the queue untouched.
 * One main-loop producer and one IRQ consumer on a single68000. These are
 * compiler barriers and atomic16-bit cursors, not a host-thread/CPU lock.
 * Neither side may be reentered. Storage/input/output must not overlap. */
u8 source_psg_queue_init(SourcePsgQueue *queue,SourcePsgEvent *storage,u16 capacity);
/* Atomically publish an entire batch, or reject without changing storage or
 * cursors. FULL requires caller backpressure/retry; bytes are never dropped.
 * Due times are unsigned32-bit ticks in a caller-supplied clock domain. All
 * pending/new events and the consumer's now must span less than2^31 ticks.
 * Batches must be ordered against the last pending event; equal times retain
 * insertion order. Empty batches are accepted with a null input pointer. */
u8 source_psg_queue_push(SourcePsgQueue *queue,const SourcePsgEvent *events,u16 count);
/* Same atomic batch contract, from separate byte/deadline sidecars. Avoids
 * allocating a second event array in a timed-reader callback. All input
 * arrays must remain valid and disjoint from queue storage until return. */
u8 source_psg_queue_push_bytes(SourcePsgQueue *queue,const u8 *values,const u32 *due,u16 count);
/* Copy and release one due event. WAIT/EMPTY/INVALID leave output untouched.
 * The caller emits the returned byte and accounts for polling/write latency.
 * This function supplies no physical clock, waiting loop or PSG register IO. */
u8 source_psg_queue_take(SourcePsgQueue *queue,u32 now,SourcePsgEvent *event);
/* Copy up to capacity due events with one validation/cursor publication.
 * OK with taken==0 covers EMPTY/WAIT/zero capacity. INVALID preserves the
 * output array, taken and cursors. Output/taken/storage must be disjoint.
 * Same single-consumer and signed deadline horizon as take. */
u8 source_psg_queue_take_many(SourcePsgQueue *queue,u32 now,SourcePsgEvent *events,u16 capacity,u16 *taken);

#endif
