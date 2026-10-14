#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "second_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(second_boss_cases)/sizeof(second_boss_cases[0]);test++)
    {
        const u8 *r=second_boss_cases[test];u8 *e=world_actor_state;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);e[0]=0x65;e[0x13]=r[5];e[0x11]=r[6];
        for(n=8;n<16;n++) world_actor_state[n*48]=n<8+r[4]?0x66:0;
        if(r[0]!=1)
        {
            e[1]=r[1];e[4]=e[0x2f]=r[2];e[5]=r[3];e[0x20]=r[7];e[0x2a]=r[7]&1;
            e[0x2b]=r[4];e[0x28]=r[11];e[0x29]=r[12];e[0x2e]=r[0]==2?20:0;
            second_boss_behavior(e,224,144,r[8],r[9],r[10],r[8]);
        }
        else
        {
            e=world_actor_state+8*48;e[0]=0x66;e[1]=r[1];e[0x20]=r[11];e[0x21]=r[12];
            second_boss_satellite_behavior(e);
        }
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
