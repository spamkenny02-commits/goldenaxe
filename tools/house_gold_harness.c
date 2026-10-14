#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "house_gold_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[7];
int main(bool hardReset)
{
 u16 test;u32 started;VDP_setEnable(FALSE);
 for(test=0;test<sizeof(house_gold_cases)/sizeof(house_gold_cases[0]);test++)
 {
  const u8 *r=house_gold_cases[test];u8 count;harness_ready=0;
  memset(game_save_state,0,sizeof(game_save_state));game_save_state[0x50+r[1]]=r[6];
  hero_gold=r[5];sound_effect_request=0;
  begin_house_gold(r[0],r[1],r[2]|((u16)r[3]<<8),r[4]);count=house_gold_remaining;
  while(house_gold_remaining) apply_house_gold_unit();
  harness_output[0]=hero_gold;harness_output[1]=game_save_state[0x50+r[1]];
  harness_output[2]=house_gold_text_pc;harness_output[3]=house_gold_text_pc>>8;
  harness_output[4]=sound_effect_request;harness_output[5]=count;harness_output[6]=house_gold_remaining;
  harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
