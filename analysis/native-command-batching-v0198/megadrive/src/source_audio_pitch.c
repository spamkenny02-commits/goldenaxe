#include "source_audio_pitch.h"
#include "source_audio_memory.h"
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)

u8 source_audio_pitch(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                      const u8 *bank,u16 return_address,u16 *de,
                      SourceClockWork *work,SourceAudioPitchOutput *output)
{
    u8 *c,mode,old_flags,saved[6],lo,hi,value;u16 base,delta,table,pointer,guard,n,original_de=*de;
    work->tstates=work->fetches=0;output->hl=0;output->unwind=0;
    if(offset>0x160) return 0;
    c=state+offset;mode=c[6];old_flags=c[0];
    for(n=0;n<6;n++) saved[n]=c[0x12+n];
    base=c[11]|((u16)c[12]<<8);output->hl=base;work->tstates=61;work->fetches=7;
    if(!mode) {ADD(11,1);return 1;}
    ADD(15,2);
    if(mode&128)
    {
        ADD(23,2);c[0x14]--;
        if(c[0x14]) {ADD(11,1);return 1;}
        ADD(163,17);c[0x14]=1;c[0x15]--;
        delta=c[0x12]|((u16)c[0x13]<<8);table=c[0x10]|((u16)c[0x11]<<8);*de=table;
        if(c[0x15]) ADD(12,1);
        else
        {
            ADD(140,18);
            if(!source_audio_read(state,low,low_bytes,bank,(u16)(table+1),&c[0x15])) goto reject;
            delta=(u16)(delta+(s8)c[0x16]);c[0x12]=delta;c[0x13]=delta>>8;
        }
        ADD(44,4);c[0x17]--;output->hl=(u16)(base+delta);
        if(c[0x17]) {ADD(11,1);return 1;}
        ADD(99,12);
        if(!source_audio_read(state,low,low_bytes,bank,(u16)(table+3),&c[0x17])) goto reject;
        c[0x16]=(u8)(-c[0x16]);return 1;
    }
    ADD(114,14);pointer=0x8a52+(mode-1)*2;
    if(!source_audio_read(state,low,low_bytes,bank,pointer,&lo) ||
       !source_audio_read(state,low,low_bytes,bank,pointer+1,&hi)) goto reject;
    table=lo|((u16)hi<<8);*de=base;
    for(guard=0;guard<256;guard++)
    {
        if(!source_audio_read(state,low,low_bytes,bank,(u16)(table+c[0x15]),&value)) goto reject;
        ADD(100,11);
        if(value<128)
        {ADD(67,7);c[0x15]++;output->hl=(u16)(base+value);return 1;}
        ADD(14,2);
        if(value==0x83)
        {
            ADD(56,6);base++;*de=base;
            if(!source_audio_read(state,low,low_bytes,bank,base,&c[0x15])) goto reject;
            continue;
        }
        ADD(7,1);
        if(value>0x83)
        {ADD(79,8);c[0x15]++;output->hl=(u16)(base+(s8)value);return 1;}
        ADD(14,2);
        if(value==0x80) {ADD(47,5);c[0x15]=0;continue;}
        ADD(50,5);c[0]|=32;output->hl=return_address;output->unwind=1;return 1;
    }
reject:
    for(n=0;n<6;n++) c[0x12+n]=saved[n];
    c[0]=old_flags;*de=original_de;work->tstates=work->fetches=0;output->hl=0;output->unwind=0;return 0;
}
