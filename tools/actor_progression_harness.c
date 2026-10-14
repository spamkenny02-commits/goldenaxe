#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actor_progression_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test;VDP_setEnable(FALSE);
    for(test=0;test<sizeof(progression_cases)/sizeof(progression_cases[0]);test++)
    {
        const u8 *row=progression_cases[test];u32 started;
        harness_ready=0;room_id=row[0]|((u16)row[1]<<8);world_dungeon_number=row[4];
        memset(game_save_state+0x1e,0,0x101);
        game_save_state[0x150+(room_id&255)]=row[2];
        game_save_state[0x1e + row[4]]=row[3];game_save_state[0x1f+row[4]]=row[3]^0xee;
        load_current_world_actors(room_id);
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
