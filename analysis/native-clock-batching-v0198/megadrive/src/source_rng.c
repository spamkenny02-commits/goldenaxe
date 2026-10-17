#include "source_rng.h"

static u8 rotate_right(u8 value)
{
    return (u8)((value>>1)|((value&1)<<7));
}

u16 source_rng_next_seed(u16 seed)
{
    u8 high=(u8)(seed>>8),low=(u8)seed;
    u8 value=rotate_right(rotate_right(high))^high;
    u16 next;
    value=rotate_right(value)^low;
    value=rotate_right(rotate_right(rotate_right(rotate_right(value))));
    value^=low;
    next=(u16)((seed<<1)+(value&1));
    return next?next:0x733c;
}

u8 source_rng_value(u16 next_seed,u8 sampled_refresh)
{
    return sampled_refresh^(u8)next_seed;
}

u8 source_refresh_advance(u8 refresh,u32 opcode_fetches)
{
    return (refresh&128)|((refresh+(opcode_fetches&127))&127);
}
