/* Test-only wrapper; production source is copied verbatim. */
#define main gaw_game_main
#include "game_main.inc"
#undef main
volatile u16 harness_case,harness_ready,harness_done;
static const u8 harness_flags[]={0,1,2,4,0x20,0x40,0x80,0xe0,0x24,0x44,0x84,0xe4,255,16,3,7};
int main(bool hardReset)
{
    u16 test,room,graphics_class,previous_class=65535;
    u32 started;
    DMA_setBufferSize(2048);
    VDP_setEnable(FALSE);
    VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setPlaneSize(64,32,TRUE);
    save_init();house_return_room=0x94;
    for(test=0;test<8192;test++)
    {
        harness_ready=0;room=test&511;
        graphics_class=room>=256?2:(room<16 || (room&15)==15)?1:0;
        if(graphics_class!=previous_class)
        { load_house_room(room,graphics_class);previous_class=graphics_class; }
        memset(game_save_state+0x50,0,256);
        game_save_state[0x50+(room&255)]=graphics_class==1?0:harness_flags[test>>9];
        if(graphics_class==1) game_save_state[0x50+0x94]=harness_flags[test>>9];
        room_id=room;world_graphics_class=graphics_class;
        decode_room_map(room,sms_vram+0x3800,world_new_md);
        harness_case=test;harness_ready=1;
        started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
