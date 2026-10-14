#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "house_quest_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[12];
int main(bool hardReset)
{
    u16 test;u8 cells[160];u32 started;
    VDP_setEnable(FALSE);
    for(test=0;test<sizeof(house_quest_cases)/sizeof(house_quest_cases[0]);test++)
    {
        const u8 *r=house_quest_cases[test];harness_ready=0;memset(cells,r[16],160);
        hero_x=(u16)r[5]<<8;hero_y=(u16)r[6]<<8;hero_items[4]=r[7];hero_basic_level=hero_items[0]=r[8];hero_armor_level=r[9];hero_shield_level=r[10];game_save_state[15]=r[11];hero_max_health=r[12];hero_items[8]=r[13];hero_items[2]=r[14];game_save_state[0x24]=r[15];
        house_quest_choose(r[0],r[1],r[2]|((u16)r[3]<<8),r[4],cells);
        harness_output[0]=hero_basic_level;harness_output[1]=hero_items[4];harness_output[2]=hero_armor_level;harness_output[3]=hero_shield_level;harness_output[4]=game_save_state[15];harness_output[5]=hero_max_health;harness_output[6]=hero_items[8];harness_output[7]=hero_items[2];harness_output[8]=game_save_state[0x24];harness_output[9]=house_quest_item;harness_output[10]=house_quest_text_pc;harness_output[11]=house_quest_text_pc>>8;
        harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
