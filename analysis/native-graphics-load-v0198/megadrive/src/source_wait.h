#ifndef GAW_SOURCE_WAIT_H
#define GAW_SOURCE_WAIT_H
#include "source_irq_context.h"
typedef struct {u16 taken;u8 error;} SourceWaitOutput;
/* Original0B95 up to0BB3 restore entry (POP AF). Clock is at first PUSH
 * opcode entry, after the source boundary check/fetch. Register/mapper
 * restoration and final RET are the caller's continuation. Context uses
 * source RAM/audio and actual per-IRQ work.
 * A failed/overlong wait leaves diagnostic partial state; caller must stop. */
u8 source_wait(SourceClock *clock,SourceIrqContext *context,SourceWaitOutput *output);
#endif
