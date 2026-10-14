#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "early_boss_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;static const u8 pairs[]={5,0,1,4,0,5};VDP_setEnable(FALSE);
    for(test=0;test<sizeof(early_boss_cases)/sizeof(early_boss_cases[0]);test++)
    {
        const u8 *r=early_boss_cases[test];u8 *e=world_actor_state;u16 n;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);
        e[1]=r[0];e[10]=r[1];e[4]=r[2];e[0x11]=96;e[0x13]=128;
        if(!r[7])
        {
            e[0]=0x63;e[0x20]=pairs[r[3]*2];e[0x21]=pairs[r[3]*2+1];
            for(n=16-r[6];n<16;n++) world_actor_state[n*48]=0;
            first_boss_behavior(e,r[4],r[5]);
        }
        else
        {
            e[0]=r[7]==1?0x72:0x73;actor_room_class=r[6];
            if(r[0]) { e[0x13]=r[3];e[0x11]=r[4]; }
            projectile_behavior(e,NULL,r[3],r[4],0,r[5]);
        }
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}

