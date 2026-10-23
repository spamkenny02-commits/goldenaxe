#ifndef GAW_SOURCE_RNG_TIMED_H
#define GAW_SOURCE_RNG_TIMED_H
#include "source_clock.h"
typedef struct {u16 seed;u8 value,sampled_refresh,zero_replaced;} SourceRngTimedOutput;
/* Original04E1 through RET. Seed is two little-endian source RAM bytes.
 * Entry follows SourceClock's prefetch convention. IRQ callbacks may change
 * RAM; already completed instruction effects are retained on callback failure.
 * This consumes a supplied source clock, never the native frame counter. */
u8 source_rng_timed(SourceClock *clock,u8 *seed,SourceRngTimedOutput *output,
                    SourceClockInterrupt interrupt,void *context);
/* Original LD A,R only: no seed update, two opcode fetches and9 T. */
u8 source_rng_read_refresh(SourceClock *clock,u8 *value,
                           SourceClockInterrupt interrupt,void *context);
#endif
