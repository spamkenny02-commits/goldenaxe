#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "composite_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(composite_boss_cases)/sizeof(composite_boss_cases[0]);test++)
    {
        const u8 *r=composite_boss_cases[test];u8 *e;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);
        for(n=8;n<16;n++) world_actor_state[n*48]=n<8+r[9]?1:0;
        world_actor_state[0]=r[5];world_actor_state[1]=r[6];world_actor_state[0x21]=r[7];
        e=world_actor_state+r[0]*48;e[0]=0x67;e[1]=r[1];e[4]=r[2];e[0x18]=r[3];e[0x1d]=r[4];
        e[0x21]=r[7];e[0x20]=r[8];e[0x13]=128;e[0x11]=96;
        composite_boss_behavior(e,r[0],r+10);
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
