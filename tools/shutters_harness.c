/* Test-only wrapper; production source is copied verbatim. */
#define main gaw_game_main
#include "game_main.inc"
#undef main
volatile u16 harness_case,harness_ready,harness_done,harness_keys;
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
        game_save_state[0x50+(graphics_class==1?0x94:(room&255))]=(const u8[]){0,0,0x0d,0xe0}[(test>>9)&3];
        decode_room_map(room,sms_vram+0x3800,world_new_md);
        hero_direction=directions[(test>>9)&3];input=buttons[(test>>9)&3];
        hero_x=xs[(test>>9)&3]<<8;hero_y=ys[(test>>9)&3]<<8;
        hero_keys=(test>>9)<4?0:(test>>9)<8?1:(test>>9)<12?2:5;
        hero_items[15]=0;hero_keys=2;
        memset(world_loot_state,0xa7,sizeof(world_loot_state));
        { u16 n,occupied=(const u8[]){7,0,6,3}[(test>>9)&3];
          for(n=0;n<7;n++) world_loot_state[n*0x30]=n<occupied?8:0; }
        world_actor_count=(const u8[]){0,1,0x80,255}[test>>11];
        room_shutter_state=room_shutter_direction=0;
        check_room_shutter((const u8[]){0x90,0xb0,0xa0,0x30}[(test>>9)&3]);if(world_room_shutter_direction[room_id&255] && world_graphics_class==2) check_dungeon_room_clear();
        if(test>=6144 && world_graphics_class==2 && world_room_shutter_direction[room_id&255]) { world_actor_count=0;check_room_shutter(0); }
        else check_room_shutter((const u8[]){0x90,0xb0,0xa0,0x30}[(test>>9)&3]);
        if(world_room_shutter_direction[room_id&255] && world_graphics_class==2) check_dungeon_room_clear();
        harness_keys=hero_keys;harness_case=test;harness_ready=1;
        started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
