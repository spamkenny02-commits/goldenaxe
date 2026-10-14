#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "dungeon_phase_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;static u8 tilemap[1280],cells[160];VDP_setEnable(FALSE);
    for(test=0;test<sizeof(dungeon_phase_cases)/sizeof(dungeon_phase_cases[0]);test++)
    {
        const u8 *r=dungeon_phase_cases[test];u8 *e=world_actor_state;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(tilemap,r[15],sizeof(tilemap));memset(cells,r[15],160);
        { u16 n;for(n=0;n<8;n++) if(r[24]&(1<<n)) world_actor_state[(8+n)*48]=0; }
        e[0]=r[0];e[1]=r[1];e[4]=r[2];e[11]=r[3];e[14]=r[4];e[13]=r[5];e[0x2e]=r[6];e[0x2f]=r[7];e[0x20]=r[8];
        e[0x13]=e[0x23]=r[9];e[0x11]=e[0x27]=r[10];e[0x2a]=r[21];e[0x2b]=r[22];e[3]=2;e[10]=1;e[12]=2;
        e[0x21]=e[0x22]=e[0x24]=e[0x25]=e[0x26]=0;
        if(r[0]==0x46)
        { actor_put_word(e,0x2e,0xffe0);e[0x28]=r[18];e[0x29]=r[19];dungeon_proximity_behavior(e,tilemap,r[11],r[12],0x100+r[13],r[14],r+16); }
        else dungeon_phase_behavior(e,cells,r[11],r[12],r[23],r[14],r+16);
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
