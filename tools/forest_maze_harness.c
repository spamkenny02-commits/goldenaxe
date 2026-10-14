/* Test-only wrapper includes the unmodified production translation. */
#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "forest_maze_cases.inc"
volatile u16 harness_case,harness_ready,harness_done,harness_room,harness_progress,harness_stage;
int main(bool hardReset)
{
    u16 test;
    DMA_setBufferSize(2048);VDP_setEnable(FALSE);
    VDP_setScreenWidth256();VDP_setScreenHeight224();VDP_setPlaneSize(64,32,TRUE);
    for(test=0;test<sizeof(maze_cases)/sizeof(maze_cases[0]);test++)
    {
        const u8 *row=maze_cases[test];u32 started;
        harness_ready=0;
        if(!row[6]) { room_id=row[0]|((u16)row[1]<<8);forest_maze_progress=row[3]; }
        world_graphics_class=row[2];hero_y=(u16)row[5]<<8;
        if(test>=480)
        {
            if(test==480) { load_house_room(0x77,0);forest_maze_progress=0; }
            hero_x=row[4]==3?0xf100:0x8000;hero_y=(u16)row[5]<<8;
            if(row[4]==0) hero_y=0x0f00;
            if(row[4]==1) hero_y=0xa100;
            begin_room_transition();step_room_transition();
        }
        else room_id=resolve_room_transition(row[4]);
        harness_room=room_id;harness_progress=forest_maze_progress;harness_stage=transition_stage;
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
