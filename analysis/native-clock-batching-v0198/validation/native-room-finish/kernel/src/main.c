#include <genesis.h>
#include "expected.h"
u8 room_finish_case(const u32 *phase,u8 refresh,u8 *ram,u8 *audio,const u8 *low,const u8 *bank6,u16 room,const u8 *map_bank,const u8 *patterns,const u8 *bank2,const u8 *bank11,const u8 *bank4,const u8 *hud,u32 *out,u32 *events,u32 *points,u8 *states);
volatile u32 gaw_finish_cases,gaw_finish_failures;
volatile u16 gaw_finish_done;
static u8 ram[336],audio[400];static u32 output[41],events[384],points[288];static u8 states[11776];
int main(bool hard_reset)
{
 u16 row,n;VDP_setEnable(FALSE);
 for(row=0;row<sizeof(cases)/sizeof(cases[0]);row++)
 {
  for(n=0;n<336;n++) ram[n]=cases[row].ram[n];
  for(n=0;n<400;n++) audio[n]=cases[row].audio[n];
  if(!room_finish_case(cases[row].phase,cases[row].refresh,ram,audio,low,bank6,cases[row].room,(cases[row].room&128)?bank9:bank8,patterns,bank2,bank11,bank4,cases[row].hud,output,events,points,states)) gaw_finish_failures++;
  for(n=0;n<41;n++) if(output[n]!=cases[row].expected[n]) gaw_finish_failures++;
  for(n=0;n<output[7]*6;n++) if(events[n]!=cases[row].events[n]) gaw_finish_failures++;
  for(n=0;n<336;n++) if(ram[n]!=cases[row].after_ram[n]) gaw_finish_failures++;
  for(n=0;n<400;n++) if(audio[n]!=cases[row].after_audio[n]) gaw_finish_failures++;
  for(n=0;n<288;n++) if(points[n]!=cases[row].points[n]) gaw_finish_failures++;
  for(n=0;n<11776;n++) if(states[n]!=cases[row].states[n]) gaw_finish_failures++;
  gaw_finish_cases++;
 }
 gaw_finish_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
