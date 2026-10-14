#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "paid_passage_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[18];
int main(bool hardReset)
{
 u16 test,n,room,outside,y,x;u32 started;u8 cells[160];VDP_setEnable(FALSE);
 for(test=0;test<sizeof(paid_passage_cases)/sizeof(paid_passage_cases[0]);test++)
 {
  const u8 *r=paid_passage_cases[test];harness_ready=0;memset(cells,0,160);
  cells[0x37]=16;cells[0x38]=r[7];cells[0x39]=1;cells[0x47]=18;cells[0x48]=19;cells[0x49]=1;
  hero_gold=r[5];sound_effect_request=0;paid_passage_cost=paid_passage_steps=paid_passage_pc=0;
  room=159;outside=r[1];y=170;x=187;game_save_state[0x50+r[9]]=r[8];
  if(!r[0])
  {
   if(begin_paid_passage(room,outside,r[2]|((u16)r[3]<<8),r[4],cells) && pay_paid_passage(r[6]==255,cells))
   { for(n=0;n<paid_passage_steps;n++) { hero_gold--;sound_effect(0x95); }open_paid_passage_cells(cells); }
  }
  else if(select_paid_passage_exit(room,outside,r[2]|((u16)r[3]<<8),r[4]))
  { room=outside=paid_passage_target;y=paid_passage_y;x=paid_passage_x;game_save_state[0x50+(room&255)]|=1; }
  harness_output[0]=hero_gold;harness_output[1]=paid_passage_cost;harness_output[2]=paid_passage_pc;harness_output[3]=paid_passage_pc>>8;
  harness_output[4]=sound_effect_request;harness_output[5]=paid_passage_steps;harness_output[6]=paid_passage_steps>>8;
  for(n=0;n<3;n++) { harness_output[7+n]=cells[0x37+n];harness_output[10+n]=cells[0x47+n]; }
  harness_output[13]=room;harness_output[14]=outside;harness_output[15]=y;harness_output[16]=x;harness_output[17]=game_save_state[0x50+r[9]];
  harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
 }
 harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
