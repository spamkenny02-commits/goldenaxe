/* Test-only wrapper; production source is copied verbatim. */
#define main gaw_game_main
#include "game_main.inc"
#undef main
volatile u16 harness_case,harness_ready,harness_done;
static const u8 directions[]={0,2,3,1},buttons[]={1,4,8,2},xs[]={128,32,224,128},ys[]={40,80,80,112};
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
        
        
        room_id=room;world_graphics_class=graphics_class;
        decode_room_map(room,sms_vram+0x3800,world_new_md);
        hero_direction=directions[(test>>9)&3];input=buttons[(test>>9)&3];
        hero_x=xs[(test>>9)&3]<<8;hero_y=ys[(test>>9)&3]<<8;
        hero_keys=(test>>9)<4?0:(test>>9)<8?1:(test>>9)<12?2:5;
        hero_items[15]=(test>>9)>=12;check_dungeon_key_door();
        harness_case=test;harness_ready=1;
        started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
