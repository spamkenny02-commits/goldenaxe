#include "source_audio_noise.h"
#include "source_audio_envelope.h"
#ifdef SGDK_GCC
#include <memory.h>
#endif
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)

static void copy_state(u8 *to,const u8 *from)
{
#ifdef SGDK_GCC
    memcpy(to,from,400);
#else
    __builtin_memcpy(to,from,400);
#endif
}

u8 source_audio_noise(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                      const u8 *bank,u16 *de,SourceClockWork *work,SourceAudioSequenceOutput *output)
{
    u8 old[400],*c,value;u16 original_de=*de;SourceClockWork sub;SourceAudioEnvelopeOutput envelope;
    work->tstates=work->fetches=0;output->de=output->count=0;output->error=output->unwind=0;
    if(offset>0x160) {output->error=255;return 0;}
    copy_state(old,state);c=state+offset;c[10]--;work->tstates=33;work->fetches=3;
    if(!c[10])
    {
        if(!source_audio_noise_sequence(state,offset,low,low_bytes,bank,&sub,output)) goto reject;
        ADD(sub.tstates,sub.fetches);*de=output->de;return 1;
    }
    ADD(17,1);
    if(!source_audio_envelope(state,offset,low,low_bytes,bank,de,&sub,&envelope)) {output->error=255;goto reject;}
    ADD(sub.tstates,sub.fetches);output->de=*de;
    if(envelope.write) output->writes[output->count++]=envelope.psg;
    if(envelope.unwind) return 1;
    ADD(20,2);
    if(c[0]&4) {ADD(11,1);return 1;}
    ADD(25,3);
    if(c[0]&16) {ADD(11,1);return 1;}
    value=(u8)(envelope.accumulator+c[8]);ADD(32,5);
    if(value&16) {ADD(14,2);value=15;}
    else ADD(12,1);
    ADD(47,5);output->writes[output->count++]=(u8)((value|c[1])+16);return 1;
reject:
    copy_state(state,old);*de=original_de;work->tstates=work->fetches=0;
    output->count=0;output->de=original_de;output->unwind=0;return 0;
}
