#ifndef GAW_SOURCE_IRQ_CONTEXT_H
#define GAW_SOURCE_IRQ_CONTEXT_H
#include "source_irq.h"
#include "source_audio_reader.h"
typedef void (*SourceIrqTrace)(void *context,const SourceClockIrq *entry,const SourceClockWork *work);
typedef struct {
    u8 *ram,*audio;
    const u8 *low,*bank6;
    u16 low_bytes,audio_de,error;
    SourceIrqInput input;
    SourceAudioReaderSink sink;
    void *sink_context;
    SourceIrqTrace trace;
    void *trace_context;
    SourceIrqOutput last_irq;
    SourceAudioReaderStatus last_audio;
    SourceClockIrq last_entry;
} SourceIrqContext;
enum {SOURCE_IRQ_CONTEXT_INVALID=0x800,SOURCE_IRQ_CONTEXT_RESET,SOURCE_IRQ_CONTEXT_NESTED};
/* SourceClockInterrupt adapter with dynamic native8000 + IRQ state/work.
 * Input lines/joy/reset/tile count are supplied by the caller; raster comes
 * from the scheduler and compensation from audio RAM. Null sink discards PSG
 * writes for timing-only use. Full IRQs crossing another VINT are explicitly
 * rejected until nested handling exists. On failure clock work is invalid;
 * streaming audio can have published earlier successful channel writes. */
u8 source_irq_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
#endif
