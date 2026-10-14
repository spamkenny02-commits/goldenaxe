#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
volatile u16 harness_done;
volatile u16 harness_wait_results[896];
int main(bool hardReset)
{
    u16 enabled,fresh,line,index=0;
    u32 started;
    VDP_setScreenWidth256();
    for(enabled=0;enabled<2;enabled++) for(fresh=0;fresh<2;fresh++)
    for(line=0;line<224;line++)
    {
        VDP_setEnable(TRUE);SYS_doVBlankProcess();
        while(GET_VCOUNTER!=line);
        if(!enabled) VDP_setEnable(FALSE);
        started=vtimer;wait_frame();
        if(fresh) while(vtimer==started);
        harness_wait_results[index++]=(u16)(vtimer-started);
    }
    VDP_setEnable(TRUE);harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
