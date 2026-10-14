/* Test-only entry point; the included production main.c is copied verbatim. */
#define main gaw_game_main
#include "game_main.inc"
#undef main
volatile u16 harness_room,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 room,graphics_class;
    u32 started;
    DMA_setBufferSize(2048);
    VDP_setEnable(FALSE);
    VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setPlaneSize(64,32,TRUE);
    save_init();
    for(room=0;room<512;room++)
    {
        harness_ready=0;
        graphics_class=room>=256?2:(room<16 || (room&15)==15)?1:0;
        world_dungeon_number=room>=256?1+(room%10):0;
        load_house_room(room,graphics_class);
        harness_room=room;harness_ready=1;
        started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
