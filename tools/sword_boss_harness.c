#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "sword_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(sword_boss_cases)/sizeof(sword_boss_cases[0]);test++)
    {
        const u8 *r=sword_boss_cases[test];u8 roll[2]={r[22],r[23]};u8 *e=world_actor_state;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);
        for(n=8;n<16;n++) world_actor_state[n*48]=n<8+r[8]?0xa7:0;
        e[0]=0x6c;e[0x13]=r[13];e[0x11]=r[14];
        if(r[0]) { e+=384;e[0]=0x74+r[0]; }
        if(r[0]==2) { e[12]=4;e[13]=6; }
        e[1]=r[1];e[4]=r[2];e[11]=r[3];e[14]=r[4];e[0x22]=r[5];e[10]=r[6];e[0x23]=r[7];
        e[0x13]=r[9];e[0x11]=r[10];memcpy(e+0x14,r+15,4);e[3]=r[19];e[0x20]=r[20];e[0x21]=r[21];
        if(!r[0]) sword_boss_behavior(e,r[11],r[12],roll);
        else if(r[0]==1) sword_boss_projectile_behavior(e,r[11],r[12]);
        else sword_boss_satellite_behavior(e);
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
