#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "conditional_house_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[10];
int main(bool hardReset)
{
 u16 test,n;u32 started;VDP_setEnable(FALSE);
 for(test=0;test<sizeof(conditional_house_cases)/sizeof(conditional_house_cases[0]);test++)
 {
  const u8 *r=conditional_house_cases[test];harness_ready=0;hero_gold=r[5];sound_effect_request=0;
  game_save_state[0x27]=r[6];game_save_state[0x22]=r[7];game_save_state[0x47]=r[8];
  conditional_house_choose(r[0],r[1],r[2]|((u16)r[3]<<8),r[4]);
  for(n=0;n<conditional_house_steps;n++) conditional_house_gold_unit();
  harness_output[0]=game_save_state[0x47];harness_output[1]=hero_gold;
  harness_output[2]=conditional_house_pc;harness_output[3]=conditional_house_pc>>8;
  harness_output[4]=conditional_house_count;harness_output[5]=conditional_house_steps;harness_output[6]=conditional_house_steps>>8;
  harness_output[7]=sound_effect_request;harness_output[8]=game_save_state[0x22];harness_output[9]=game_save_state[0x27];
  harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
