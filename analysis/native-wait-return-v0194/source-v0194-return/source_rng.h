#ifndef GAW_SOURCE_RNG_H
#define GAW_SOURCE_RNG_H
#include <types.h>

/* 04E1 recurrence. The caller supplies R at LD A,R, after instruction
 * fetches and any intervening interrupts have advanced the source clock.
 * These helpers do not estimate R from the Mega Drive frame counter. */
u16 source_rng_next_seed(u16 seed);
u8 source_rng_value(u16 next_seed,u8 sampled_refresh);
u8 source_refresh_advance(u8 refresh,u32 opcode_fetches);

#endif
