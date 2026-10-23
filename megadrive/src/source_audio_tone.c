#include "source_audio_tone.h"
#include "source_audio_pitch.h"
#include "source_audio_envelope.h"
#include "source_audio_memory.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)
#define READ(a,v) do {if(!source_audio_read(state,low,low_bytes,bank,(u16)(a),&(v))) goto reject;} while(0)
#ifndef GAW_AUDIO_TIMED_STAMP
#define GAW_AUDIO_TIMED_STAMP(o,t) ((void)0)
#endif
#ifdef EMIT
#undef EMIT
#endif
#define EMIT(v,t) do {if(output->count>=512) goto reject;GAW_AUDIO_TIMED_STAMP(output,t);output->writes[output->count++]=(u8)(v);} while(0)

#ifndef GAW_AUDIO_STREAM_CHANNELS
static void copy_state(u8 *to,const u8 *from,u16 bytes)
{
#ifdef SGDK_GCC
    memcpy(to,from,bytes);
#else
    __builtin_memcpy(to,from,bytes);
#endif
}
#endif

u8 source_audio_tone(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                     const u8 *bank,u16 *de,SourceClockWork *work,
                     SourceAudioSequenceOutput *output)
{
#ifndef GAW_AUDIO_STREAM_CHANNELS
    /* Without a sequence step, tone/pitch/envelope only mutate this
     * 48-byte record. A sequence can restore or change other channels. */
    u8 old[400],*backup_base;u16 backup_bytes;
#endif
    u8 *c,pitch=1,n,value;u16 original_de=*de,pointer,frequency;
    SourceClockWork sub;SourceAudioPitchOutput modulation;SourceAudioEnvelopeOutput envelope;
#ifdef GAW_AUDIO_TIMED_TONE
    u16 timed_index;
#endif
    work->tstates=work->fetches=0;output->de=*de;output->count=output->error=output->unwind=0;
    if(offset>0x160) {output->error=255;return 0;}

#ifndef GAW_AUDIO_STREAM_CHANNELS
    backup_bytes=state[offset+10]==1?400:48;
    backup_base=backup_bytes==400?state:state+offset;
    copy_state(old,backup_base,backup_bytes);
#endif
    c=state+offset;c[10]--;ADD(23,2);
    if(!c[10])
    {
        ADD(24,2);
        if(!source_audio_sequence(state,offset,low,low_bytes,bank,&sub,output)) goto reject;
#ifdef GAW_AUDIO_TIMED_TONE
        for(timed_index=0;timed_index<output->count;timed_index++) output->write_tstates[timed_index]+=47;
#endif
        ADD(sub.tstates,sub.fetches);*de=output->de;
        if(output->unwind) {output->unwind=0;goto done;}
        *de=c[3]|((u16)c[4]<<8);
        for(n=0;n<2;n++)
        {
            ADD(20,2);
            if(c[0]&(n?4:16)) {ADD(11,1);goto done;}
            ADD(5,1);
        }
        ADD(37,3);
        if(!(c[6]&128)) ADD(11,1);
        else
        {
            ADD(25,3);
            if(c[0]&2) ADD(11,1);
            else
            {
                ADD(5+19+19+15+10+7+7+11+4+3*16+7+8+7+4+19+19+10,
                    1+2+2+2+1+1+1+1+1+3*2+1+2+1+1+2+2+1);
                pointer=c[16]|((u16)c[17]<<8);
                for(n=0;n<3;n++) {READ(pointer+n,value);c[20+n]=value;}
                READ(pointer+3,value);c[23]=value>>1;c[18]=c[19]=0;
                *de=0xde00+offset+23;
            }
        }
        ADD(37,3);
        if(!(c[7]&128)) ADD(11,1);
        else
        {
            ADD(25,3);
            if(c[0]&2) ADD(11,1);
            else
            {
                ADD(25,3);
                if(c[29]&128) ADD(11,1);
                else {c[31]=255;c[29]=16|c[30];ADD(5+7+19+7+19+19+10,1+1+2+1+2+2+1);}
            }
        }
        ADD(12,1);
    }
    else
    {
        ADD(32,3);
        if(c[0]&4) {ADD(11,1);goto done;}
        ADD(28,4);
        if(!c[14]) ADD(12,1);
        else
        {
            ADD(30,3);c[14]--;
            if(c[14]) ADD(10,1);
            else
            {
                ADD(37,3);
                if(c[0]&2) ADD(11,1);
                else
                {
                    ADD(35,4);
                    if(c[7]&128) {c[29]=(c[29]&15)|128;ADD(62,7);}
                    else
                    {
                        c[0]|=16;ADD(43,4);
                        if(c[0]&4) ADD(11,1);
                        else {ADD(52,6);EMIT(c[1]+31,work->tstates-10);}
                    }
                }
            }
        }
        ADD(23,3);
        if(!c[6]) {ADD(12,1);pitch=0;}
        else
        {
            ADD(27,3);
            if(c[0]&32) {ADD(12,1);pitch=0;}
            else ADD(7,1);
        }
    }
    if(pitch)
    {
        ADD(20,2);
        if(c[0]&64) ADD(12,1);
        else
        {
            ADD(24,2);
            if(!source_audio_pitch(state,offset,low,low_bytes,bank,0x8507,de,&sub,&modulation)) goto reject;
            ADD(sub.tstates,sub.fetches);
            if(modulation.unwind) goto done;
            *de=(u16)(s16)(s8)c[37];frequency=(u16)(modulation.hl+*de);
            ADD(7+19+4+10+((c[37]&128)?4:0)+4+11+19+7,
                1+2+1+1+((c[37]&128)?1:0)+1+1+2+1);
            if(c[1]==224) ADD(14,2);else ADD(12,1);
            ADD(4+4+7+4+11+4+7+4+4*4+11,1+1+1+1+1+1+1+1+4+1);
            EMIT((c[1]==224?192:c[1])|(frequency&15),work->tstates-42);
            value=(u8)((frequency&0xf0)|(frequency>>8));
            EMIT((value<<4)|(value>>4),work->tstates);
        }
    }
    ADD(17,1);
    if(!source_audio_envelope(state,offset,low,low_bytes,bank,de,&sub,&envelope)) goto reject;
    ADD(sub.tstates,sub.fetches);
    if(envelope.write) EMIT(envelope.psg,work->tstates-10);
    if(envelope.unwind) goto done;
    for(n=0;n<2;n++)
    {
        ADD(20,2);
        if(c[0]&(n?16:4)) {ADD(11,1);goto done;}
        ADD(5,1);
    }
    value=(u8)(envelope.accumulator+c[8]);
    ADD(19+8+((value&16)?14:12)+19+7+11+10,2+2+((value&16)?2:1)+2+1+1+1);
    if(value&16) value=15;
    EMIT((value|c[1])+16,work->tstates-10);
done:
    output->de=*de;return 1;
reject:

#ifndef GAW_AUDIO_STREAM_CHANNELS
    copy_state(backup_base,old,backup_bytes);
#endif
    *de=original_de;work->tstates=work->fetches=0;
    output->de=original_de;output->count=output->unwind=0;
    if(!output->error) output->error=255;
    return 0;
}
