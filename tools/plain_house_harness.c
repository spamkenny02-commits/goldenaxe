#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "plain_house_cases.inc"
#include "plain_house_source_pcs.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[2];
int main(bool hardReset)
{
 u16 test;u32 started;VDP_setEnable(FALSE);
 for(test=0;test<sizeof(plain_house_cases)/sizeof(plain_house_cases[0]);test++)
 {
  const u8 *r=plain_house_cases[test];u16 selected,pc;harness_ready=0;
  selected=select_plain_house_dialogue(r[0],r[1],r[2]|((u16)r[3]<<8),r[4]);pc=selected==65535?0:plain_house_source_pcs[selected];
  harness_output[0]=pc;harness_output[1]=pc>>8;harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
