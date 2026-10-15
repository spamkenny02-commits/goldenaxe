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
        sound_ram[0xd0]=r[1];sound_ram[0xd1]=0xe0;sound_ram[0x18]=r[2];sound_ram[0x17]=r[3];
        sound_ram[0x3e]=r[0];PSG_write(0xe6);PSG_write(0xf0);
        sound_noise_note(sound_ram+0xd0,r[0]);
        harness_case=n;harness_ready=1;started=vtimer;
        while(vtimer-started<3) SYS_doVBlankProcess();
    }
    harness_ready=0;harness_done=1;
    while(TRUE) SYS_doVBlankProcess();
    return 0;
}
