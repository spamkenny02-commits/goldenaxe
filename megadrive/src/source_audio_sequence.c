#include "source_audio_sequence.h"
#include "source_audio_memory.h"
#include "source_audio_priority.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)
#define READ(a,v) do {if(!source_audio_read(state,low,low_bytes,bank,(u16)(a),&(v))) goto reject;} while(0)
#define WORD(a,v) do {READ((a),lo);READ((u16)((a)+1),hi);(v)=lo|((u16)hi<<8);} while(0)
#define PUT(i,v) do {c[(i)]=(u8)(v);c[(i)+1]=(u16)(v)>>8;} while(0)
#ifndef GAW_AUDIO_TIMED_STAMP
#define GAW_AUDIO_TIMED_STAMP(o,t) ((void)0)
#endif
#ifdef EMIT
#undef EMIT
#endif
#define EMIT(v,t) do {if(output->count>=512) goto reject;GAW_AUDIO_TIMED_STAMP(output,t);output->writes[output->count++]=(u8)(v);} while(0)

#ifndef GAW_AUDIO_STREAM_CHANNELS
static void copy_state(u8 *to,const u8 *from)
{
#ifdef SGDK_GCC
    memcpy(to,from,400);
#else
    __builtin_memcpy(to,from,400);
#endif
}
#endif
static u8 duration(u8 value,u8 scale,SourceClockWork *work)
{
    if(scale==1) {work->tstates+=34;work->fetches+=4;}
    else {work->tstates+=37+17*(u16)(u8)(scale-1);work->fetches+=6+2*(u16)(u8)(scale-1);}
    return (u8)(value*scale);
}

static u8 noise_note(u8 *state,u16 offset,u8 note,SourceClockWork *work,SourceAudioSequenceOutput *output)
{
    static const u8 settings[6][3]={{1,4,0xe4},{3,6,0xe4},{1,1,0xe6},{2,3,0xe5},{3,3,0xe6},{4,4,0xe4}};
    u8 *c=state+offset;u16 bit;
    for(bit=0;bit<6;bit++)
    {
        ADD(8,2);
        if(note&(1<<bit))
        {
            ADD(12+21+(bit?12:0),4+(bit?1:0));c[7]=settings[bit][0];c[8]=state[24]+settings[bit][1];ADD(75,8);
            if(c[0]&4) ADD(11,1);
            else {ADD(56,6);state[19]=state[23]+settings[bit][2];EMIT(state[19],work->tstates-10);}
            return 1;
        }
        ADD(7,1);
    }
    c[0]|=16;ADD(53,5);
    if(c[0]&4) ADD(11,1);
    else {ADD(52,6);EMIT(c[1]+31,work->tstates-10);}
    return 1;
reject:return 0;
}

static u8 sequence(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                    const u8 *bank,u8 noise,SourceClockWork *work,SourceAudioSequenceOutput *output)
{
#ifndef GAW_AUDIO_STREAM_CHANNELS
    u8 old[400];
#endif
    u8 *c,note=0xff,value,lo,hi,old_stereo,mask,amount;
    u16 cursor=0,guard,index,stack,target,background,frequency,n;
    SourceClockWork restored;SourceAudioDispatchOutput writes;
#ifdef GAW_AUDIO_TIMED_SEQUENCE
    u32 restore_time;
#endif
    work->tstates=work->fetches=0;output->de=output->count=0;output->unwind=output->error=0;
    if(offset>0x160) {output->error=0xff;return 0;}

#ifndef GAW_AUDIO_STREAM_CHANNELS
    copy_state(old,state);
#endif
    c=state+offset;cursor=c[3]|((u16)c[4]<<8);c[0]&=(u8)~(noise?16:18);
    ADD(noise?61:84,noise?6:8);
    for(guard=0;guard<256;guard++)
    {
        READ(cursor,note);cursor++;ADD(noise?20:30,noise?3:4);
        if(note<0xe0) break;
        if(note==0xe3 || note==0xec || note==0xef || note>=0xfe) goto reject;
        if(note==0xf1 || note==0xf2)
        {
            ADD(noise?121:99,noise?16:14);
            if(note==0xf1) {state[0x12]=128;ADD(20,2);}
            ADD(26,3);
            if(c[1]==0xa0) {ADD(22,2);background=0x70;}
            else
            {
                ADD(14,2);
                if(c[1]==0xc0)
                {
                    ADD(34,4);
                    if(state[0x160]&128) {ADD(12,1);background=0x160;}
                    else {ADD(29,3);background=0xa0;}
                }
                else
                {
                    ADD(27,3);
                    if(c[0]&64) ADD(12,1);
                    else
                    {
                        ADD(39,5);
                        if(!(state[0x130]&128))
                        {ADD(75,9);state[0xa0]=(state[0xa0]&(u8)~68)|16;state[0x130]=0;}
                    }
                    ADD(22,2);background=0xd0;
                }
            }
            state[background]=(state[background]&(u8)~4)|16;state[17]=0;c[0]=0;
            EMIT(c[1]|31,work->tstates+48);
            ADD(15+15+7+11+4+13+19+13+4,2+2+1+1+1+1+2+1+1);
            if(state[14])
            {
                ADD(7+17,1+1);
#ifdef GAW_AUDIO_TIMED_SEQUENCE
                /* 8211 begins CALL8261. The latch's OUT precedes EX AF/RET
                 * by14T; zero/nonzero DE0F select121/126T from8211 entry. */
                restore_time=work->tstates+(state[15]?126:121);
#endif
                if(!source_audio_restore(state,bank,state[14],&cursor,&restored,&writes)) goto reject;
                ADD(restored.tstates,restored.fetches);
                for(n=0;n<writes.count;n++) EMIT(writes.writes[n],restore_time);
            }
            else ADD(12,1);
            ADD(30,3);output->unwind=noise?2:1;output->de=cursor;return 1;
        }
        ADD(noise?139:115,noise?18:16);READ(cursor,value);
        switch(note)
        {
            case 0xe0:case 0xe9:
                c[7]=128;for(n=0;n<5;n++) READ((u16)(cursor+n),c[0x20+n]);
                cursor+=5;ADD(19+15+10+7+7+11+4+5*16+4+6+10,2+2+1+1+1+1+1+5*2+1+1+1);break;
            case 0xe1:case 0xee:case 0xf4:case 0xf5:case 0xfa:
                index=note==0xe1?0x25:note==0xee?0x1c:note==0xf4?6:note==0xf5?7:2;
                c[index]=value;cursor++;ADD(29,3);break;
            case 0xe2:
                old_stereo=c[0x26];mask=value^255;c[0x26]=value;ADD(72,9);
                for(n=0;n<3;n++)
                {
                    if(c[1]==0x80+n*0x20) {ADD(12,1);break;}
                    ADD(23,5);old_stereo=(u8)((old_stereo<<1)|(old_stereo>>7));mask=(u8)((mask<<1)|(mask>>7));
                    if(n!=2) ADD(7,1);
                }
                state[0x12]=(state[0x12]|old_stereo)&mask;cursor++;ADD(53,7);break;
            case 0xe4:state[24]=(state[24]+value)&15;cursor++;ADD(51,6);break;
            case 0xe5:c[0x1e]=value?8:0;cursor++;ADD(4+(value?14:12)+19+10,1+(value?2:1)+2+1);break;
            case 0xe6:
                ADD(21,3);
                if(state[11]) ADD(11,1);
                else {ADD(64,8);c[8]=(c[8]+value)&15;}
                cursor++;break;
            case 0xe7:c[0]|=2;ADD(39,4);break;
            case 0xe8:
                ADD(17,1);c[14]=c[15]=duration(value,c[2],work);cursor++;ADD(48,5);break;
            case 0xea:
                ADD(8,2);
                if(value&128)
                {
                    c[0]|=1;c[0x18]=value;cursor++;READ(cursor,c[0x19]);c[0x1a]=c[0x19];
                    ADD(110,12);
                }
                else {c[0]&=(u8)~1;c[0x1a]=0;cursor++;ADD(70,7);}
                cursor++;break;
            case 0xeb:case 0xfc:cursor++;ADD(10,1);break;
            case 0xed:state[1]=state[2]=value;cursor++;ADD(36,3);break;
            case 0xf0:PUT(0x10,cursor);c[6]=128;cursor+=4;ADD(85,10);break;
            case 0xf3:
                ADD(31,4);
                if(!(state[15]&128))
                {
                    ADD(15,3);
                    if((value&3)!=3) ADD(12,1);
                    else
                    {
                        ADD(29,4);
                        if(!(state[0x130]&128)) ADD(12,1);
                        else
                        {
                            ADD(7+10+15+15+4+19+4+11+13+10+10+10-(noise?18:16),1+1+2+2+1+2+1+1+1+1+1+1-2);
                            state[0xd0]=(state[0xd0]&(u8)~4)|16;c[0]=0;state[15]=255;
                            EMIT(255,work->tstates-43);output->unwind=noise?2:1;output->de=cursor;return 1;
                        }
                    }
                }
                /* Command dispatch already counts the future INC/JP return
                 * trampoline (16T tonal,18T noise). OUT is inside F3. */
                EMIT(value,work->tstates+18-(noise?18:16));ADD(53,7);
                if((value&3)==3)
                {ADD(96,10);EMIT(0xdf,work->tstates-71-(noise?18:16));c[0]&=(u8)~64;state[0xa0]|=4;state[0x130]|=4;}
                else
                {
                    ADD(55,5);c[0]|=64;
                    if(state[0x130]&128) {ADD(45,4);state[0x130]&=(u8)~4;}
                    else {ADD(32,4);state[0xa0]&=(u8)~4;}
                }
                cursor++;break;
            case 0xf6:WORD(cursor,target);cursor=target;ADD(40,6);break;
            case 0xf7:
                index=(u8)(value+0x27);cursor++;
                if(offset+index>=400) goto reject;
                ADD(71,10);
                if(c[index]) ADD(12,1);
                else {READ(cursor,c[index]);ADD(21,3);}
                cursor++;c[index]--;ADD(27,3);
                if(c[index]) {WORD(cursor,target);cursor=target;ADD(40,6);}
                else {cursor+=2;ADD(16,2);}
                break;
            case 0xf8:
                WORD(cursor,target);stack=(u8)(c[9]-2);
                if(offset+stack+1>=400) goto reject;
                PUT(stack,(u16)(cursor+1));c[9]=stack;cursor=target;
                ADD(4+6+7+4+11+15+10+23+19+23+7+11+7+6+7+10+6+10,1+1+1+1+1+2+1+2+2+2+1+1+1+1+1+1+1+1);break;
            case 0xf9:
                stack=c[9];if(offset+stack+1>=400) goto reject;
                cursor=(u16)((c[stack]|((u16)c[stack+1]<<8))+1);c[9]=(u8)(stack+2);
                ADD(15+10+19+7+11+7+6+7+23+23+10,2+1+2+1+1+1+1+1+2+2+1);break;
            case 0xfb:c[5]+=value;cursor++;ADD(48,5);break;
            case 0xfd:c[0]=(c[0]&(u8)~8)|(value==1?8:0);cursor++;ADD(7+(value==1?7:12)+23+10,5);break;
            default:goto reject;
        }
    }
    if(guard==256) goto reject;
    if(noise)
    {
        ADD(24,3);
        if(note>=128)
        {
            ADD(17,1);if(!noise_note(state,offset,note,work,output)) goto reject;ADD(10,1);
            READ(cursor,amount);cursor++;ADD(27,4);
            if(amount&128) {c[10]=c[13];cursor--;ADD(56,6);}
            else {ADD(17,1);c[10]=c[13]=duration(amount,c[2],work);ADD(38,4);}
        }
        else {ADD(17,1);c[10]=c[13]=duration(note,c[2],work);ADD(38,4);}
        goto store;
    }
    ADD(30,3);
    if(c[0]&8)
    {
        READ(cursor,lo);cursor++;frequency=((u16)note<<8)|lo;ADD(25,5);
        if(!frequency) ADD(12,1);
        else {ADD(7+7+19+4+4+10+((c[5]&128)?4:0)+11,1+1+2+1+1+1+((c[5]&128)?1:0)+1);frequency=(u16)(frequency+(s8)c[5]);}
        PUT(11,frequency);ADD(61,7);READ(cursor,amount);cursor++;
        ADD(17,1);c[10]=c[13]=duration(amount,c[2],work);ADD(38,4);
    }
    else
    {
        ADD(7,1);
        if(note<128) {ADD(12+17,2);c[10]=c[13]=duration(note,c[2],work);ADD(38,4);}
        else
        {
            ADD(7,1);
            if(note==128)
            {
                ADD(12+17+20,1+1+2);
                if(c[0]&2) ADD(11,1);
                else
                {
                    ADD(35,4);
                    if(c[7]&128) {ADD(62,7);c[0x1d]=(c[0x1d]&15)|128;}
                    else
                    {
                        ADD(43,4);c[0]|=16;
                        if(c[0]&4) ADD(11,1);
                        else {ADD(52,6);EMIT(c[1]+31,work->tstates-10);}
                    }
                }
                ADD(12,1);
            }
            else
            {
                ADD(7+4+19+7+19+4+17+7+19+10+67+19+19,1+1+2+1+2+1+1+1+2+1+9+2+2);
                c[0x1d]&=127;index=(u8)((note&127)+c[5]);WORD(0x843d+index*2,frequency);PUT(11,frequency);
            }
            READ(cursor,amount);cursor++;ADD(27,4);
            if(amount&128) {c[10]=c[13];cursor--;ADD(56,6);}
            else {ADD(17,1);c[10]=c[13]=duration(amount,c[2],work);ADD(38,4);}
        }
    }
store:
    PUT(3,cursor);ADD(58,6);output->de=cursor;
    if(c[0]&2) {ADD(11,1);return 1;}
    ADD(25,3);
    if(c[0]&64) ADD(12,1);
    else {ADD(30,3);c[0]&=(u8)~32;}
    ADD(81,9);c[14]=c[15];c[0x15]=0;
    if(c[7]&128) ADD(11,1);
    else {c[0x1f]=0;ADD(34,4);}
    return 1;
reject:

#ifndef GAW_AUDIO_STREAM_CHANNELS
    copy_state(state,old);
#endif
    work->tstates=work->fetches=0;output->de=output->count=0;
    output->unwind=0;output->error=note;return 0;
}

u8 source_audio_sequence(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                         const u8 *bank,SourceClockWork *work,SourceAudioSequenceOutput *output)
{return sequence(state,offset,low,low_bytes,bank,0,work,output);}

u8 source_audio_noise_sequence(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                               const u8 *bank,SourceClockWork *work,SourceAudioSequenceOutput *output)
{return sequence(state,offset,low,low_bytes,bank,1,work,output);}

u8 source_audio_noise_note(u8 *state,u16 offset,u8 note,SourceClockWork *work,SourceAudioSequenceOutput *output)
{
    work->tstates=work->fetches=0;output->de=output->count=0;output->error=output->unwind=0;
    if(offset>0x160) {output->error=255;return 0;}
    return noise_note(state,offset,note,work,output);
}
