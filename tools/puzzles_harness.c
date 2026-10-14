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
        { u16 mode=test>>9,n;u8 flags=(const u8[]){0x14,0x94,0x54,0x34,0x10,0x15,0x04,0x14,0x14,0x14,0x14,0x14,0xb4,0x14,0x14,0x14}[mode];
          game_save_state[0x50+(graphics_class==1?0x94:(room&255))]=(const u8[]){0,0,0,0,0,0,0,0,4,0xe0,255,0,0,0,0,0}[mode];
          decode_room_map(room,sms_vram+0x3800,world_new_md);
          hero_keys=2;world_actor_count=mode==15?0:1;
          room_shutter_state=room_shutter_direction=0;room_script_coordinate=65535;
          memset(world_loot_state,0xa7,sizeof(world_loot_state));
          { u16 slot,occupied=(const u8[]){7,0,6,3}[mode&3];
            for(slot=0;slot<7;slot++) world_loot_state[slot*0x30]=slot<occupied?8:0; }
          for(n=0;n<31;n++) if(world_room_puzzles[n][0]==room) break;
          if(n<31 && graphics_class==2)
          {
              const u16 *r=world_room_puzzles[n];room_script_coordinate=r[2]^(mode==7?2:0);
              if(mode==13) scratch[0x84e]=0;
              check_room_puzzle(flags,0);check_room_contact(flags);check_room_shutter(flags);check_dungeon_room_clear();check_room_puzzle(flags,1);
              check_room_puzzle(flags,0);check_room_contact(flags);check_room_shutter(flags);check_dungeon_room_clear();check_room_puzzle(flags,1);
          }
        }
        harness_keys=hero_keys;harness_case=test;harness_ready=1;
        started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
