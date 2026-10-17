#ifndef GAW_SOURCE_WAIT_RESTORE_H
#define GAW_SOURCE_WAIT_RESTORE_H
#include "source_wait.h"
/* 0BB3..0BC5 including RET; returns at caller opcode entry after boundary/fetch.
 * Native caller variables/resources retain their own state; original register
 * and mapper restoration instructions contribute their exact source work.
 * IRQs can run between every instruction. Failure leaves diagnostic state. */
u8 source_wait_restore(SourceClock *clock,SourceIrqContext *context);
u8 source_wait_complete(SourceClock *clock,SourceIrqContext *context,SourceWaitOutput *output);
#endif
