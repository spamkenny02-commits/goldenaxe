#include "source_audio_priority.h"
#ifndef GAW_AUDIO_PREFIX_STAMP
#define GAW_AUDIO_PREFIX_STAMP(o,t) ((void)0)
#endif
#ifndef GAW_AUDIO_PREFIX_REBASE
#define GAW_AUDIO_PREFIX_REBASE(o,t) ((void)0)
#endif

static void latch(u8 *state,u8 command,SourceClockWork *work,SourceAudioDispatchOutput *output)
{
    u16 target;state[14]=command;work->tstates=58;work->fetches=7;
    if(!(state[15]&128))
    {
        target=state[15]?0x160:0x130;state[target]=state[15];
        GAW_AUDIO_PREFIX_STAMP(output,work->tstates+(state[15]?65:60)-14);
        output->writes[output->count++]=(u8)(state[target+1]+31);
        work->tstates+=state[15]?65:60;work->fetches+=state[15]?8:7;
    }
}

u8 source_audio_restore(u8 *state,const u8 *bank,u8 command,u16 *de,
                       SourceClockWork *work,SourceAudioDispatchOutput *output)
{
    u16 index,header,channel,target,background,n;
    work->tstates=work->fetches=0;output->mute=output->count=0;
    if(command<0x90 || command>0xac) return 0;
    latch(state,command,work,output);GAW_AUDIO_PREFIX_REBASE(output,17);work->tstates+=150;work->fetches+=18;
    index=0xb30+(command-0x90)*2;header=bank[index]|((u16)bank[index+1]<<8);
    channel=bank[header-0x8000+2];header++;
    if(channel!=0xc0)
    {
        work->tstates+=52;work->fetches+=7;*de=0xdf60;target=0x160;background=0xd0;
        if(state[target]&128)
        { state[15]=state[target];work->tstates+=23;work->fetches+=2;return 1; }
        work->tstates+=19;work->fetches+=2;state[15]=1;
    }
    else
    {
        work->tstates+=39;work->fetches+=4;
        if(state[0x160]&128)
        {
            work->tstates+=14;work->fetches+=2;
            if(!(state[0x160]&64))
            { state[15]=128;work->tstates+=35;work->fetches+=3;return 1; }
            work->tstates+=7;work->fetches++;
        }
        work->tstates+=45;work->fetches+=6;*de=0xdf30;target=0x130;background=0xa0;
        if(state[target]&128)
        { state[15]=state[target];work->tstates+=23;work->fetches+=2;return 1; }
        work->tstates+=4;work->fetches++;state[15]=0;
    }
    work->tstates+=367;work->fetches+=44;state[background]|=4;
    for(n=0;n<9;n++) state[target+n]=bank[header-0x8000+n];
    state[target+9]=0x30;state[target+10]=1;
    state[target+0x27]=state[target+0x28]=state[target+0x29]=0;
    *de=0xde00+target+0x30;return 1;
}

u8 source_audio_priority(u8 *state,const u8 *bank,u16 *de,SourceClockWork *work,
                        SourceAudioDispatchOutput *output)
{
    u8 request=state[9],priority,command;SourceClockWork restored;
    work->tstates=work->fetches=0;output->mute=output->count=0;
    if(request!=0 && request!=128)
    {
        if(request<0x90 || request>0xac) return 0;
        priority=bank[0xad4+(request&127)];
        command=priority<state[16]?state[14]:request;
        if(command<0x90 || command>0xac) return 0;
    }
    else {priority=command=0;}
    *de=0xde09;work->tstates=24;work->fetches=3;
    if(request==128)
    {
        latch(state,0,&restored,output);GAW_AUDIO_PREFIX_REBASE(output,47);state[9]=0;
        work->tstates+=23+restored.tstates;work->fetches+=3+restored.fetches;return 1;
    }
    work->tstates+=14;work->fetches+=2;
    if(!request) {work->tstates+=11;work->fetches++;return 1;}
    work->tstates+=112;work->fetches+=14;
    if(priority<state[16]) {work->tstates+=12;work->fetches++;}
    else
    {state[16]=priority&127;state[14]=request;work->tstates+=59;work->fetches+=7;}
    state[9]=0;*de=0xde0a;work->tstates+=46;work->fetches+=6;
    source_audio_restore(state,bank,command,de,&restored,output);
    GAW_AUDIO_PREFIX_REBASE(output,work->tstates);
    work->tstates+=restored.tstates;work->fetches+=restored.fetches;return 1;
}
