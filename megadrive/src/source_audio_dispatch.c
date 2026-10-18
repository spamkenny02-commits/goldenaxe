#include "source_audio_dispatch.h"
#ifndef GAW_AUDIO_PREFIX_STAMP
#define GAW_AUDIO_PREFIX_STAMP(o,t) ((void)0)
#endif
#ifndef GAW_AUDIO_PREFIX_MUTE
#define GAW_AUDIO_PREFIX_MUTE(o,t) ((void)0)
#endif

#define POINTER_T 67
#define POINTER_M1 9
#define COPY_T 321
#define COPY_M1 40

static u16 pointer(const u8 *bank,u16 address)
{ return bank[address-0x8000]|((u16)bank[address-0x7fff]<<8); }

static void copy_channel(u8 *state,const u8 *bank,u16 offset,u16 header)
{
    u16 n;
    for(n=0;n<9;n++) state[offset+n]=bank[header-0x8000+n];
    state[offset+9]=0x30;state[offset+10]=1;
    state[offset+0x27]=state[offset+0x28]=state[offset+0x29]=0;
}

static void stop(u8 *state,SourceClockWork *work,SourceAudioDispatchOutput *output)
{
    SourceClockWork stopped;source_audio_stop(state,&stopped);
    work->tstates+=stopped.tstates;work->fetches+=stopped.fetches;output->mute=1;
    GAW_AUDIO_PREFIX_MUTE(output,work->tstates-249);
}

static void finish(u8 *state,SourceClockWork *work)
{ state[5]=128;work->tstates+=30;work->fetches+=3; }

u8 source_audio_dispatch(u8 *state,const u8 *bank,SourceClockWork *work,
                         SourceAudioDispatchOutput *output)
{
    u16 command=state[5],index,header,count,n,channel,offset,background;
    work->tstates=work->fetches=0;output->mute=output->count=0;
    if(command==0x8e || command==0x8f || (command>=0xad && command<=0xaf) || command==0xb4)
        return 0;
    work->tstates=31;work->fetches=4;
    if(!(command&128)) { stop(state,work,output);return 1; }
    work->tstates+=7;work->fetches++;
    if(command<0x90)
    {
        work->tstates+=19;work->fetches+=2;
        if(command==0x80) { work->tstates+=11;work->fetches++;return 1; }
        work->tstates+=26;work->fetches+=3;stop(state,work,output);
        index=command-0x81;
        work->tstates+=104;work->fetches+=12;
        state[1]=state[2]=bank[0xb09+index];
        work->tstates+=10+17+POINTER_T+7+6+10;work->fetches+=2+POINTER_M1+3;
        header=pointer(bank,0x8b16+index*2);count=bank[header++-0x8000];
        for(n=0;n<count;n++)
        {
            copy_channel(state,bank,0x40+n*0x30,header+n*9);
            work->tstates+=17+COPY_T+(n+1==count?8:13);
            work->fetches+=1+COPY_M1+1;
        }
        finish(state,work);return 1;
    }
    work->tstates+=14;work->fetches+=2;
    if(command<0xad)
    {
        work->tstates+=12+13+7+10+17+POINTER_T+7+6;
        work->fetches+=5+POINTER_M1+2;state[15]=command;
        header=pointer(bank,0x8b30+(command-0x90)*2);count=bank[header++-0x8000];
        for(n=0;n<count;n++,header+=9)
        {
            channel=bank[header-0x8000+1];work->tstates+=26;work->fetches+=4;
            if(channel==0xa0)
            { work->tstates+=36;work->fetches+=4;offset=0x100;background=0x70; }
            else
            {
                work->tstates+=14;work->fetches+=2;
                if(channel==0xc0)
                {
                    work->tstates+=46;work->fetches+=5;
                    if(state[0x160]&64) { work->tstates+=12;work->fetches++; }
                    else
                    {
                        work->tstates+=48;work->fetches+=5;state[0x160]|=4;
                        GAW_AUDIO_PREFIX_STAMP(output,work->tstates);output->writes[output->count++]=0xff;
                    }
                    work->tstates+=36;work->fetches+=4;offset=0x130;background=0xa0;
                }
                else { work->tstates+=43;work->fetches+=5;offset=0x160;background=0xd0; }
            }
            work->tstates+=17+23+COPY_T+(n+1==count?8:13);
            work->fetches+=1+2+COPY_M1+1;
            state[background]|=4;copy_channel(state,bank,offset,header);
        }
        work->tstates+=12;work->fetches++;finish(state,work);return 1;
    }
    work->tstates+=24;work->fetches+=3;
    if(command>=0xb5) { stop(state,work,output);return 1; }
    work->tstates+=7+10+17+POINTER_T+4;work->fetches+=3+POINTER_M1+1;
    if(command==0xb0)
    {
        state[11]=12;state[12]=state[13]=18;
        work->tstates+=63;work->fetches+=6;finish(state,work);
    }
    else if(command==0xb1) stop(state,work,output);
    else if(command==0xb2)
    {
        work->tstates+=41;work->fetches+=5;
        for(n=0;n<3;n++)
        {
            state[0x103+n*0x30]=0x4e;state[0x104+n*0x30]=0x81;
            work->tstates+=53+(n==2?8:13);work->fetches+=7;
        }
        work->tstates+=10;work->fetches++;
    }
    else
    {
        state[14]=0;work->tstates+=65;work->fetches+=7;
        if(!(state[15]&128))
        {
            work->tstates+=10+(state[15]?17:12)+7+6+7+7+11;
            work->fetches+=state[15]?8:7;
            offset=state[15]?0x160:0x130;state[offset]=state[15];
            GAW_AUDIO_PREFIX_STAMP(output,work->tstates);output->writes[output->count++]=(u8)(state[offset+1]+31);
        }
        work->tstates+=24;work->fetches+=3;finish(state,work);
    }
    return 1;
}
