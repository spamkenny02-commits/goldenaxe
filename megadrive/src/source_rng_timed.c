#include "source_rng_timed.h"
#include "source_rng.h"
#define S(t,m) do {if(!source_clock_plain(clock,t,m,interrupt,context)) return 0;} while(0)
u8 source_rng_read_refresh(SourceClock *clock,u8 *value,
                           SourceClockInterrupt interrupt,void *context)
{
 if(!clock || !value) return 0;
 S(9,2);*value=clock->refresh;return 1;
}
u8 source_rng_timed(SourceClock *clock,u8 *seed,SourceRngTimedOutput *output,
                    SourceClockInterrupt interrupt,void *context)
{
 u16 old,next;u8 before,fallback,n;
 if(!clock || !seed || !output) return 0;
 old=seed[0]|((u16)seed[1]<<8);fallback=old==0;before=clock->refresh;
 /* Stable fast path: no instruction boundary can accept an interrupt inside
  * this span. Preserve the exact R sample at ED5F, before the final3 M1. */
 if(source_clock_block(clock,fallback?135:130,fallback?22:21))
 {
  next=source_rng_next_seed(old);output->sampled_refresh=source_refresh_advance(before,18+fallback);
  seed[0]=next;seed[1]=next>>8;
 }
 else
 {
  S(16,1);old=seed[0]|((u16)seed[1]<<8);fallback=old==0;
  S(4,1);S(4,1);S(4,1);S(4,1);S(4,1);S(4,1);
  for(n=0;n<4;n++) S(4,1);
  S(4,1);S(4,1);S(15,2);next=source_rng_next_seed(old);
  S(fallback?7:12,1);if(fallback) S(10,1);
  S(9,2);output->sampled_refresh=clock->refresh;
  S(4,1);S(16,1);seed[0]=next;seed[1]=next>>8;
  S(10,1);
 }
 output->seed=next;
 output->value=source_rng_value(next,output->sampled_refresh);output->zero_replaced=fallback;
 return 1;
}
#undef S
