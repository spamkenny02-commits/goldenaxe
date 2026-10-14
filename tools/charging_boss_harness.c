#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "charging_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(charging_boss_cases)/sizeof(charging_boss_cases[0]);test++)
    {
        const u8 *r=charging_boss_cases[test];u8 *e=world_actor_state;u8 roll[4]={r[12],r[13],r[14],r[11]};u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);e[0]=r[0];e[1]=r[1];e[4]=r[2];e[0x13]=r[3];e[0x11]=r[4];
        e[10]=e[0x20]=e[0x22]=r[7];e[0x21]=r[8];e[0x25]=r[9];
        charging_boss_behavior(e,r[5],r[6],roll,r[15]);
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
