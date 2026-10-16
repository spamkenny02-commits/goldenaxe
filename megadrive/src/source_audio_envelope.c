#include "source_audio_envelope.h"
#include "source_audio_memory.h"
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)

static void mute(u8 *channel,SourceClockWork *work,SourceAudioEnvelopeOutput *output)
{
    channel[0]|=16;ADD(43,4);
    if(channel[0]&4) ADD(11,1);
    else
    {
        ADD(52,6);output->write=1;output->psg=(u8)(channel[1]+31);
        output->accumulator=output->psg;
    }
}

u8 source_audio_envelope(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                         const u8 *bank,u16 *de,SourceClockWork *work,
                         SourceAudioEnvelopeOutput *output)
{
    u8 *c,mode,flags,old_flags,old_index,lo,hi,byte;
    u16 value,step,limit,pointer,table,guard,original_de=*de;
    work->tstates=work->fetches=0;
    output->accumulator=output->unwind=output->write=output->psg=0;
    if(offset>0x160) return 0;
    c=state+offset;mode=c[7];work->tstates=23;work->fetches=3;
    if(!mode) {ADD(11,1);return 1;}
    if(mode&128)
    {
        flags=c[0x1d];value=c[0x1f];ADD(35,4);
        if((flags&32) && !(flags&16)) *de=((u16)c[0x21]<<8)|c[0x22];
        else *de=((u16)c[(flags&16)?0x20:(flags&64)?0x23:0x24]<<8)|(*de&255);
        if(flags&16)
        {
            ADD(49,6);step=c[0x20];
            if(value>=step) {ADD(12,1);value-=step;}
            else {ADD(11,2);value=0;}
            ADD(23,3);c[0x1f]=value;
            if(value) ADD(12,1);
            else {ADD(64,7);c[0x1d]^=0x30;}
        }
        else
        {
            ADD(32,3);
            if(flags&32)
            {
                ADD(68,8);limit=c[0x22];value+=c[0x21];
                if(value>255) {ADD(16,2);value=limit;}
                else
                {
                    ADD(11,2);
                    if(value<limit) ADD(12,1);
                    else {ADD(11,2);value=limit;}
                }
                ADD(23,3);c[0x1f]=value;
                if(value!=limit) ADD(12,1);
                else
                {
                    ADD(46,5);
                    if(flags&8) {ADD(26,3);c[0x1d]^=0x30;}
                    else {ADD(19,2);c[0x1d]^=0x60;}
                    ADD(31,3);
                }
            }
            else
            {
                ADD(32,3);
                if(flags&64)
                {
                    ADD(49,6);value+=c[0x23];
                    if(value<=255) ADD(12,1);
                    else {ADD(14,2);value=255;}
                    ADD(26,3);c[0x1f]=value;
                    if(value!=255) ADD(12,1);
                    else {ADD(64,7);c[0x1d]&=0x8f;}
                }
                else
                {
                    ADD(54,6);value+=c[0x24];
                    if(value<=255) {ADD(31,3);c[0x1f]=value;}
                    else
                    {
                        ADD(88,10);c[0x1d]&=15;c[0x1f]=255;
                        output->accumulator=255;mute(c,work,output);return 1;
                    }
                }
            }
        }
        ADD(52,8);output->accumulator=c[0x1f]>>4;return 1;
    }
    old_flags=c[0];old_index=c[0x1f];ADD(125,15);
    pointer=0x897f+(mode-1)*2;
    if(!source_audio_read(state,low,low_bytes,bank,pointer,&lo) ||
       !source_audio_read(state,low,low_bytes,bank,pointer+1,&hi)) goto reject;
    table=lo|((u16)hi<<8);
    for(guard=0;guard<256;guard++)
    {
        if(!source_audio_read(state,low,low_bytes,bank,(u16)(table+c[0x1f]),&byte)) goto reject;
        ADD(100,11);output->accumulator=byte;
        if(byte<128) {c[0x1f]++;ADD(45,4);return 1;}
        ADD(14,2);
        if(byte==0x82)
        {ADD(57,5);output->unwind=1;mute(c,work,output);return 1;}
        ADD(14,2);
        if(byte==0x81)
        {c[0]|=16;ADD(55,5);output->unwind=1;return 1;}
        ADD(14,2);
        if(byte==0x80) {ADD(28,3);c[0x1f]=0;}
        else
        {
            ADD(32,4);(*de)++;
            if(!source_audio_read(state,low,low_bytes,bank,*de,&c[0x1f])) goto reject;
        }
        ADD(19,2);
    }
reject:
    c[0]=old_flags;c[0x1f]=old_index;*de=original_de;
    work->tstates=work->fetches=0;
    output->accumulator=output->unwind=output->write=output->psg=0;return 0;
}
