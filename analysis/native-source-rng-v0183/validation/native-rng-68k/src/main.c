#include <genesis.h>
#include "../../../megadrive/src/source_rng.h"
#include "expected.h"
volatile u32 gaw_rng_seed_cases,gaw_rng_output_cases,gaw_rng_refresh_cases,gaw_rng_failures;
volatile u16 gaw_rng_done;
int main(bool hard_reset)
{
 u32 seed,low,high,r,n,count;u16 highs[3]={0,0x8000,0xff00};
 const u32 wide_counts[5]={256UL,65535UL,65536UL,0x80000000UL,0xffffffffUL};
 VDP_setEnable(FALSE);
 for(seed=0;seed<65536UL;seed++) { if(source_rng_next_seed((u16)seed)!=expected_seed[seed]) gaw_rng_failures++;gaw_rng_seed_cases++; }
 for(high=0;high<3;high++) for(low=0;low<256;low++) for(r=0;r<256;r++)
 { if(source_rng_value(highs[high]|low,r)!=(r^low)) gaw_rng_failures++;gaw_rng_output_cases++; }
 for(r=0;r<256;r++) for(n=0;n<261;n++)
 { count=n<256?n:wide_counts[n-256];if(source_refresh_advance(r,count)!=((r&128)|((r+(count&127))&127))) gaw_rng_failures++;gaw_rng_refresh_cases++; }
 gaw_rng_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
