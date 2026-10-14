#define main gaw_game_main
#include "game_main.inc"
#undef main
volatile u16 harness_case,harness_clock,harness_pending,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 test,tile;u32 started;
    VDP_setEnable(FALSE);world_graphics_class=2;
    for(test=0;test<8192;test++)
    {
        harness_ready=0;tile=(test>>8)*8;scratch[0x30]=tile;
        memset(sms_vram+tile*32,0xa7,192);dungeon_bitmap_pending=0;
        world_clock_shift=vtimer-(test&255);animate_dungeon_bitmaps();
        harness_clock=world_clock();harness_pending=dungeon_bitmap_pending;
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
