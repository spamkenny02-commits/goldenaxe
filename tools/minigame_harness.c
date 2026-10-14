#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "minigame_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[73];
int main(bool hardReset)
{
 u16 test,n,cell,steps,rng;u32 started;u8 cells[160],count;u16 pc;
 VDP_setEnable(FALSE);
 for(test=0;test<sizeof(minigame_cases)/sizeof(minigame_cases[0]);test++)
 {
  const u8 *r=minigame_cases[test];harness_ready=0;memset(cells,0,160);
  for(n=0x33;n<0x3d;n++) cells[n]=0x3a;
  cells[12]=r[6];cells[3]=r[7];cells[6]=r[8];cells[9]=r[9];
  hero_gold=r[5];minigame_stage=r[12];sound_effect_request=0;steps=rng=pc=count=0;
  if(!r[0])
  {
   cell=minigame_select(r[1]|((u16)r[2]<<8),r[3],cells);
   if(cell!=65535)
   {
    rng=1;if(!minigame_draw(cells,cell,r[4])) { rng++;minigame_draw(cells,cell,0); }
    sound_effect_request=0x95;if(cells[cell]>=0x38) pc=cells[cell]==0x38?0xb9d7:0xba20;
   }
  }
  else if(r[0]==1) { cells[0x33]=r[11];minigame_flip(cells,0x33); }
  else
  {
   minigame_prepare_reward(hero_gold,cells);count=minigame_reward_count;pc=minigame_reward_pc;steps=minigame_reward_steps;
   for(n=0;n<steps;n++) { hero_gold=(u8)(hero_gold+minigame_reward_delta);sound_effect_request=0x95; }
  }
  memcpy((void *)harness_output,cells,64);harness_output[64]=minigame_stage;harness_output[65]=hero_gold;
  harness_output[66]=pc;harness_output[67]=pc>>8;harness_output[68]=count;harness_output[69]=steps;harness_output[70]=steps>>8;harness_output[71]=sound_effect_request;harness_output[72]=rng;
  harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
