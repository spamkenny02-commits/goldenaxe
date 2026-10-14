#include <genesis.h>
#include "ending_credits.inc"
volatile u16 harness_case,harness_ready,harness_done;
volatile u8 harness_output[73];
int main(bool hardReset)
{
    EndingCredits state={0,0,0,0x7e00,0,0};u8 line[64];u32 started;u16 n;
    VDP_setEnable(FALSE);ending_credit_row(&state,line);
    while(TRUE)
    {
        harness_ready=0;
        harness_output[0]=state.wait;harness_output[1]=state.done;
        harness_output[2]=state.scroll;harness_output[3]=state.scroll>>8;
        harness_output[4]=state.row;harness_output[5]=state.row>>8;
        harness_output[6]=state.text;harness_output[7]=0xc9+(state.text>>8);
        harness_output[8]=state.vscroll;
        for(n=0;n<64;n++) harness_output[9+n]=line[n];
        harness_ready=1;started=vtimer;while(vtimer-started<3) SYS_doVBlankProcess();
        if(state.done) break;
        harness_case++;ending_credit_tick(&state,line);
    }
    harness_ready=0;harness_done=1;while(TRUE) SYS_doVBlankProcess();return 0;
}
