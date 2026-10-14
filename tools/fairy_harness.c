#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "fairy_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[11];
int main(bool hardReset)
{
 u16 test,steps;u32 started;VDP_setEnable(FALSE);
 for(test=0;test<sizeof(fairy_cases)/sizeof(fairy_cases[0]);test++)
 {
  const u8 *r=fairy_cases[test];harness_ready=0;steps=0;sound_effect_request=0;
  hero_max_health=r[5];hero_health=r[6];hero_max_magic=r[7];hero_magic=r[8];game_save_state[0x50+r[1]]=r[9];
  if(begin_fairy(r[0],r[1],r[2]|((u16)r[3]<<8),r[4]))
  {
   fairy_apply_capacity();if(fairy_item==42) while(hero_health!=hero_max_health) { fairy_health_unit();steps++; }
  }
  harness_output[0]=game_save_state[0x50+r[1]];harness_output[1]=hero_health;harness_output[2]=hero_max_health;
  harness_output[3]=hero_magic;harness_output[4]=hero_max_magic;harness_output[5]=fairy_item;
  harness_output[6]=fairy_text_pc;harness_output[7]=fairy_text_pc>>8;harness_output[8]=sound_effect_request;
  harness_output[9]=steps;harness_output[10]=steps>>8;
  harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
