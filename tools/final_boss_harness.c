#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "final_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(final_boss_cases)/sizeof(final_boss_cases[0]);test++)
    {
        const u8 *r=final_boss_cases[test];u8 roll[2]={r[17],r[18]};u8 *e=world_actor_state;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);
        for(n=8;n<16;n++) world_actor_state[n*48]=n<8+r[6]?0xa7:0;
        e[0]=0x6d;e[1]=r[0];e[4]=r[1];e[5]=r[2];e[11]=r[3];e[14]=r[4];e[0x23]=r[5];
        e[0x13]=r[7];e[0x11]=r[8];e[10]=r[11];e[0x22]=r[12];e[3]=r[13];e[0x1d]=r[14];memcpy(e+0x14,r+19,4);
        hero_selected_item=r[15];hero_weapon_level=r[16];
        final_boss_behavior(e,r[9],r[10],roll,world_final_boss_weapon_valid());
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
