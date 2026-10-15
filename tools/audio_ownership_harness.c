#define main gaw_game_main
#include "game_main.inc"
#undef main
#include "actors.inc"
#include "cases.inc"
volatile u16 harness_case,harness_ready,harness_done;
int main(bool hardReset)
{
    u16 n;u32 started;
    for(n=0;n<sizeof(raw_cases)/sizeof(raw_cases[0]);n++)
    {
        const u8 *r=raw_cases[n];harness_ready=0;
        memcpy(sound_ram,raw_seed,400);
        sound_ram[0x40]=r[0];sound_ram[0x41]=r[1];sound_ram[0x0f]=r[2];sound_ram[0x130]=r[3];
        sound_ram[0x43]=0x2b;sound_ram[0x44]=0x9b;
        sound_sequence(sound_ram+0x40,FALSE);
        harness_case=n;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_ready=0;harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
