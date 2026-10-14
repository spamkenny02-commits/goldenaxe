#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "dungeon_curse_cases.inc"
volatile u16 harness_case,harness_ready,harness_done,harness_curse,harness_defense,harness_palette0,harness_palette1;
int main(bool hardReset)
{
    u16 test;static u8 tilemap[1280],cells[160];VDP_setEnable(FALSE);
    for(test=0;test<sizeof(dungeon_curse_cases)/sizeof(dungeon_curse_cases[0]);test++)
    {
        const u8 *r=dungeon_curse_cases[test];u8 *e=world_actor_state+r[14]*48;u32 started;u16 n,free=r[24]|((u16)r[25]<<8);
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(tilemap,r[15],1280);memset(cells,r[15],160);
        hero_armor_level=r[24];hero_shield_level=r[25];world_clock_shift=vtimer-r[23];
        e[0]=r[0];e[1]=r[1];e[4]=r[2];e[11]=r[3];e[14]=r[4];e[13]=r[5];e[0x20]=r[6];e[0x21]=r[7];e[10]=r[8];e[0x13]=r[9];e[0x11]=r[10];e[0x18]=r[21];e[0x1d]=r[22];e[0x22]=r[26];e[5]=0;e[3]=r[27];e[12]=2;
        memcpy(e+0x14,r+28,4);
        game_save_state[15]=r[22];dungeon_curse_behavior(e,tilemap,cells,r[11],r[12],r[23],r[14],r+16);prepare_hero_defense();prepare_hero_armor_palette();harness_curse=game_save_state[15];harness_defense=hero_defense;harness_palette0=sms_palette[22];harness_palette1=sms_palette[23];
        harness_case=test;harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
