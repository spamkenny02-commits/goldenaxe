#include <genesis.h>
#include "expected.h"
u8 prefix_fast_case(const u32*,u8,u8*,u8*,const u8*,const u8*,const u8*,u16,u32*,u32*,u8*);
u8 prefix_scalar_case(const u32*,u8,u8*,u8*,const u8*,const u8*,const u8*,u16,u32*,u32*,u8*);
u8 shared_pixels[16384];static u8 expected_pixels[16384],ram[2][336],audio[2][400];
static u32 output[2][20],events[2][384];
volatile u32 gaw_window_cases,gaw_window_failures;volatile u16 gaw_window_done;
int main(bool hard_reset)
{
 u16 row,n;
 VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[0][n]=ram[1][n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[0][n]=audio[1][n]=cases[row].audio[n];
  for(n=0;n<384;n++) events[0][n]=events[1][n]=0;
  if(!prefix_fast_case(cases[row].phase,cases[row].refresh,ram[0],audio[0],low,bank6,cases[row].stream,0,output[0],events[0],expected_pixels)) gaw_window_failures++;
  if(!prefix_scalar_case(cases[row].phase,cases[row].refresh,ram[1],audio[1],low,bank6,cases[row].stream,0,output[1],events[1],expected_pixels)) gaw_window_failures++;
  for(n=0;n<20;n++) if(output[0][n]!=output[1][n]) gaw_window_failures++;
  for(n=0;n<336;n++) if(ram[0][n]!=ram[1][n]) gaw_window_failures++;
  for(n=0;n<400;n++) if(audio[0][n]!=audio[1][n]) gaw_window_failures++;
  for(n=0;n<384;n++) if(events[0][n]!=events[1][n]) gaw_window_failures++;
  gaw_window_cases++;
 }
 gaw_window_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
