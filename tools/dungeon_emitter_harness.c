#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "dungeon_emitter_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;static u8 tilemap[1280],cells[160];VDP_setEnable(FALSE);
    for(test=0;test<sizeof(dungeon_emitter_cases)/sizeof(dungeon_emitter_cases[0]);test++)
    {
        const u8 *r=dungeon_emitter_cases[test];u8 *e=world_actor_state+r[14]*48;u32 started;u16 n,free=r[24]|((u16)r[25]<<8);
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(tilemap,r[15],1280);memset(cells,r[15],160);
        for(n=0;n<16;n++) if(free&(1<<n)) world_actor_state[n*48]=0;
        e[0]=r[0];e[1]=r[1];e[4]=r[2];e[11]=r[3];e[14]=r[4];e[13]=r[5];e[0x20]=r[6];e[0x21]=r[7];e[10]=r[8];e[0x13]=r[9];e[0x11]=r[10];e[0x18]=r[21];e[0x1d]=r[22];e[0x2c]=r[26];e[5]=r[27];e[3]=2;e[12]=2;
        actor_room_class=1;
        if(r[0]==0x71) projectile_behavior(e,tilemap,r[11],r[12],r[23],r[14]);
        else dungeon_emitter_behavior(e,256+r[13],r[14],r[11],r[12],r+16);
        harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
