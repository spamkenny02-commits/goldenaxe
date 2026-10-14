#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "boss_death_cases.inc"
volatile u16 harness_case,harness_ready,harness_done,harness_effect,harness_hero,harness_game,harness_count;
volatile u8 harness_progress[256];
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(boss_death_cases)/sizeof(boss_death_cases[0]);test++)
    {
        const u8 *row=boss_death_cases[test];u8 *e=world_actor_state;u32 started;
        harness_ready=0;memset(world_actor_state,0xa7,768);memset(game_save_state+0x1e,0,256);
        hero_state=1;game_state=12;world_actor_count=8;sound_effect_request=0;
        e[0]=7;e[1]=0;e[0x11]=96;e[0x13]=128;
        if(!row[0])
        {
            e[0x13]=row[1];e[0x11]=row[2];world_actor_state[(8+row[4])*0x30]=0;
            spawn_world_boss_particle(e,row[3]);
        }
        else
        { world_dungeon_number=row[1];e[1]=row[2];e[0x28]=row[3];tick_world_boss_death(e); }
        { u16 n;for(n=0;n<256;n++) harness_progress[n]=game_save_state[0x1e + n]; }
        harness_hero=hero_state;harness_game=game_state;harness_count=world_actor_count;
        harness_effect=sound_effect_request;harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
