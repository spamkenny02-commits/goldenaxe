#include <genesis.h>
#include "expected.h"
u8 clock_case(const u32 *input,const u16 *plan,u16 length,u32 *out);
volatile u32 gaw_clock_cases,gaw_clock_failures,gaw_clock_rejections;
volatile u16 gaw_clock_done;
int main(bool hard_reset)
{
 u32 i,output[18];u16 n;u8 accepted;VDP_setEnable(FALSE);
 for(i=0;i<sizeof(cases)/sizeof(cases[0]);i++)
 {
  accepted=clock_case(cases[i].input,plans[cases[i].plan],lengths[cases[i].plan],output);
  if(accepted!=cases[i].accepted) gaw_clock_failures++;
  if(accepted) { for(n=0;n<18;n++) if(output[n]!=cases[i].expected[n]) gaw_clock_failures++; }
  else gaw_clock_rejections++;
  gaw_clock_cases++;
 }
 gaw_clock_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
