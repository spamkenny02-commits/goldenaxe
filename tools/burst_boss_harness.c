#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "burst_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(burst_boss_cases)/sizeof(burst_boss_cases[0]);test++)
    {
        const u8 *r=burst_boss_cases[test];u8 cells[160],roll[2]={r[15],r[5]};u8 *e=world_actor_state;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(cells,r[14],160);
        for(n=8;n<16;n++) world_actor_state[n*48]=!r[0] && n<8+r[6]?0xa7:0;
        e[0]=r[1];if(r[0]) { e+=384;e[0]=0x74; }
        e[1]=r[2];e[4]=r[3];e[11]=r[4];e[14]=r[5];e[0x22]=r[6];e[10]=r[7];e[0x13]=r[10];e[0x11]=r[11];
        if(!r[0]) burst_boss_behavior(e,cells,r[12],r[13],r[8],r[9],roll);
        else { actor_room_class=r[14];burst_boss_projectile_behavior(e); }
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
