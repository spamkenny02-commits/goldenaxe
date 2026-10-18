#ifndef GAW_SOURCE_IRQ_TIMED_CONTEXT_H
#define GAW_SOURCE_IRQ_TIMED_CONTEXT_H
#include "source_irq_context.h"
#include "source_audio_timed.h"

/* Deadlines are unsigned source-master ticks since the SourceClock epoch.
 * Each packet is a successful prefix/channel list, at most512 bytes. The
 * sink copies retained data before returning; no hardware clock or pacing is
 * supplied here. core.sink is unused by this adapter. core.trace still runs
 * at successful IRQ commit. Error/reset/nested publication follows the base
 * adapter contract; earlier stream packets may already have been emitted. */
typedef void (*SourceIrqTimedSink)(void *context,const u8 *writes,const u32 *master,u16 count);
typedef struct {
    SourceIrqContext core; /* First member: pass &ctx.core to existing loaders. */
    SourceIrqTimedSink sink;
    void *sink_context;
    u32 reader_entry_master;
} SourceTimedIrqContext;

u8 source_irq_timed_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
/* Same layout/master dates with the fast timed reader's failure contract. */
u8 source_irq_fast_timed_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
/* Identical fast dates/contract, with fused helper-to-master conversion. */
u8 source_irq_master_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
#endif
