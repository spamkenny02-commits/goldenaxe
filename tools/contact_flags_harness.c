#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "contact_flags_cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_result[8];
static void capture(u16 offset,u8 flags)
{
    harness_result[offset]=flags;
    harness_result[offset+1]=room_script_coordinate;
    harness_result[offset+2]=room_script_coordinate>>8;
    harness_result[offset+3]=room_script_direction;
}
int main(bool hardReset)
{
    u16 test;u32 started;
    VDP_setEnable(FALSE);
    for(test=0;test<8192;test++)
    {
        const u8 *c=cases[test];harness_ready=0;
        hero_x=(u16)c[0]<<8;hero_y=(u16)c[1]<<8;hero_direction=c[2];input=c[3];
        room_script_coordinate=c[8]|((u16)c[9]<<8);room_script_direction=c[10];room_script_coordinate_pending=c[11];
        capture(0,room_script_flags(c[4],c[5],c[12]));
        hero_x=(u16)(c[0]^1)<<8;hero_direction^=1;input^=1;
        capture(4,room_script_flags(c[4],c[5],c[12]));
        harness_case=test;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
