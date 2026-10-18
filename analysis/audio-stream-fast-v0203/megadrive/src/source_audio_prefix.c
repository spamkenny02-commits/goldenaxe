#include "source_audio_prefix.h"

u8 source_audio_gate(u8 *state,SourceClockWork *work)
{
    if(!state[10]) { work->tstates=33;work->fetches=4;return 0; }
    if(!(state[10]&128)) { work->tstates=39;work->fetches=5;return 1; }
    state[10]--;state[5]=128;
    work->tstates=365;work->fetches=38;return 1;
}

void source_audio_arbitrate(u8 *state,const u8 *bank6,SourceClockWork *work)
{
    u16 offset;work->tstates=72;work->fetches=7;
    for(offset=6;offset<=8;offset++)
    {
        u8 request=state[offset],index=request&127;
        work->tstates+=14;
        if(!index) { work->tstates+=12;work->fetches+=7; }
        else
        {
            u8 priority=bank6[0xad4+index];work->tstates+=69;
            if(priority<state[0x11]) { work->tstates+=12;work->fetches+=16; }
            else
            {
                work->tstates+=59;work->fetches+=22;
                state[0x11]=priority&127;state[5]=request;
            }
        }
        work->tstates+=27;state[offset]=0;
    }
}

void source_audio_tempo(u8 *state,SourceClockWork *work)
{
    u16 channel;
    if(!state[1]) { work->tstates=32;work->fetches=4;return; }
    if(--state[1]) { work->tstates=48;work->fetches=6;return; }
    state[1]=state[2];
    for(channel=0;channel<4;channel++) state[0x4a+channel*0x30]++;
    work->tstates=234;work->fetches=24;
}

void source_audio_stop(u8 *state,SourceClockWork *work)
{
    u16 n;for(n=5;n<SOURCE_AUDIO_BYTES;n++) state[n]=0;
    state[5]=128;work->tstates=8683;work->fetches=829;
}

static void fade_volume(u8 *state,u16 offset,SourceClockWork *work)
{
    u8 value=(u8)(state[offset]+1);
    if(value>=12) { work->tstates=29;work->fetches=4; }
    else { state[offset]=value;work->tstates=40;work->fetches=6; }
}

void source_audio_fade(u8 *state,SourceClockWork *work)
{
    u16 channel;SourceClockWork volume;
    if(!state[11]) { work->tstates=28;work->fetches=3;return; }
    if(--state[12]) { work->tstates=69;work->fetches=8;return; }
    state[12]=state[13];
    if(!--state[11])
    { source_audio_stop(state,work);work->tstates+=117;work->fetches+=12;return; }
    work->tstates=144;work->fetches=15;
    for(channel=0;channel<3;channel++)
    {
        fade_volume(state,0x48+channel*0x30,&volume);
        work->tstates+=17+volume.tstates+11+(channel==2?8:13);
        work->fetches+=3+volume.fetches;
    }
    fade_volume(state,0x18,&volume);
    work->tstates+=10+volume.tstates;work->fetches+=1+volume.fetches;
}
