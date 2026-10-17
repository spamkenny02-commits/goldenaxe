#include <genesis.h>
#include "expected.h"
u8 repeat_pair(u16,u32,u8,u8,u8,u8,u8,u16,u8,u16,u32*);
volatile u32 gaw_repeat_cases,gaw_repeat_failures;volatile u16 gaw_repeat_done;
static u32 output[34];
int main(bool hard_reset)
{
 u16 r,n;VDP_setEnable(FALSE);
 for(r=0;r<sizeof(cases)/sizeof(cases[0]);r++)
 {
  const u32 *v=cases[r].input;
  if(!repeat_pair(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9],output)) gaw_repeat_failures++;
  if(output[0]!=cases[r].accepted || output[1]!=cases[r].accepted) gaw_repeat_failures++;
  for(n=0;n<16;n++) if(output[2+n]!=cases[r].state[n] || output[18+n]!=cases[r].state[n]) gaw_repeat_failures++;
  gaw_repeat_cases++;
 }
 gaw_repeat_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
