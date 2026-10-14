#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "dungeon_thief_cases.inc"
volatile u16 harness_case,harness_ready,harness_done,harness_state,harness_counter,harness_anim,harness_hp,harness_gold,harness_sound,harness_y,harness_x;
int main(bool hardReset)
{
    u16 test;static u8 tilemap[1280],cells[160];VDP_setEnable(FALSE);
    for(test=0;test<sizeof(dungeon_thief_cases)/sizeof(dungeon_thief_cases[0]);test++)
    {
        const u8 *r=dungeon_thief_cases[test];u8 *e=world_actor_state+r[14]*48;u32 started;u16 n,free=r[24]|((u16)r[25]<<8);
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(tilemap,r[15],1280);memset(cells,r[15],160);

        e[0]=r[0];e[1]=r[1];e[4]=r[2];e[11]=r[3];e[14]=r[4];e[13]=r[5];e[0x20]=r[6];e[0x21]=r[7];e[10]=r[8];e[0x13]=r[9];e[0x11]=r[10];e[0x18]=r[21];e[0x1d]=0;e[5]=0;e[3]=r[29];e[12]=2;
        actor_room_class=1;
        hero_state=r[24];hero_counter=r[25];hero_animation=r[26];hero_health=r[22];hero_gold=r[27];input=r[28];world_previous_input=0;
        hero_x=(r[11]<<8)|r[30];hero_y=(r[12]<<8)|r[31];sound_effect_request=0;
        dungeon_thief_behavior(e,tilemap,cells,r[11],r[12],r[23],r[14],r+16);
        harness_state=hero_state;harness_counter=hero_counter;harness_anim=hero_animation;harness_hp=hero_health;harness_gold=hero_gold;harness_sound=sound_effect_request;harness_y=hero_y;harness_x=hero_x;
        harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
