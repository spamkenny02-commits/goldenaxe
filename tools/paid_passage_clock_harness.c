#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u16 harness_clock_before,harness_clock_after,harness_room,harness_mask;
volatile u32 harness_elapsed;
int main(bool hardReset)
{
    const u16 rooms[]={0x1a,0x3c,0x36,0x87,0x6d,0x96};
    u16 n,mask;u32 started,hold;
    VDP_setScreenWidth256();VDP_setPlaneSize(32,32,TRUE);
    hero_basic_level=hero_armor_level=hero_shield_level=1;hero_health=hero_max_health=24;
    hero_magic=hero_max_magic=24;hero_gold=10;
    for(n=0;n<6;n++) for(mask=0;mask<256;mask++)
    {
        harness_ready=0;room_id=0x9f;world_graphics_class=1;
        hero_x=0x8800;hero_y=0x5000;
        game_save_state[0x50+rooms[n]]=1;
        game_save_state[0x150+rooms[n]]=mask;
        paid_passage_target=rooms[n];
        world_clock_shift=vtimer-mask;harness_clock_before=world_clock();
        started=vtimer;load_paid_passage_room();
        harness_elapsed=vtimer-started;harness_clock_after=world_clock();
        harness_room=room_id;harness_mask=mask;
        harness_case=n*256+mask;harness_ready=1;
        hold=vtimer;while(vtimer-hold<3) SYS_doVBlankProcess();
    }
    harness_ready=0;harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
