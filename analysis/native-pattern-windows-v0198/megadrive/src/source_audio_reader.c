#include "source_audio_reader.h"
#include "source_audio_dispatch.h"
#include "source_audio_priority.h"
#include "source_audio_tone.h"
#include "source_audio_noise.h"
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

static void emit(SourceAudioReaderStatus *status,SourceAudioReaderSink sink,void *context,
                 const u8 *writes,u16 count)
{
    if(count) {sink(context,writes,count);status->count+=count;}
}

u8 source_audio_reader_stream(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                              u16 *de,SourceClockWork *work,SourceAudioReaderStatus *output,
                              SourceAudioReaderSink sink,void *context)
{
    u8 gate=state[10],fade_stopping,phase;u16 offset;
    SourceClockWork sub;SourceAudioDispatchOutput dispatch;SourceAudioSequenceOutput channel;
    output->count=output->error=output->track=0;
    if(source_audio_gate(state,work))
    {if(gate&128) emit(output,sink,context,bank+0x412,10);return 1;}
    source_audio_arbitrate(state,bank,&sub);ADD(17+sub.tstates,1+sub.fetches);
    source_audio_tempo(state,&sub);ADD(17+sub.tstates,1+sub.fetches);
    fade_stopping=(state[11]==1 && state[12]==1);
    source_audio_fade(state,&sub);ADD(17+sub.tstates,1+sub.fetches);
    if(fade_stopping) emit(output,sink,context,bank+0x412,10);
    phase=state[5];
    if(!source_audio_dispatch(state,bank,&sub,&dispatch))
    {output->error=0x100|phase;goto reject;}
    ADD(17+sub.tstates,1+sub.fetches);
    if(phase>=0x81 && phase<=0x8d) output->track=phase;
    if(dispatch.mute) emit(output,sink,context,bank+0x412,10);
    emit(output,sink,context,dispatch.writes,dispatch.count);
    if(!source_audio_priority(state,bank,de,&sub,&dispatch))
    {output->error=0x200|state[9];goto reject;}
    ADD(17+sub.tstates,1+sub.fetches);
    emit(output,sink,context,dispatch.writes,dispatch.count);
    ADD(27,3);
    if(state[3])
    {
        ADD(24,3);phase=(u8)(state[4]+1);
        if(phase<6) ADD(12,1);
        else {ADD(11,2);phase=0;}
        state[4]=phase;ADD(17,2);
        if(!phase) {ADD(11,1);return 1;}
        ADD(5,1);
    }
    for(offset=0x40;offset<=0x160;offset+=0x30)
    {
        ADD(34,4);
        if(!(state[offset]&128)) {ADD(10,1);continue;}
        ADD(17,1);
        if(offset==0xd0)
        {
            if(!source_audio_noise(state,offset,low,low_bytes,bank,de,&sub,&channel))
            {output->error=0x600|channel.error;goto reject;}
        }
        else if(!source_audio_tone(state,offset,low,low_bytes,bank,de,&sub,&channel))
        {output->error=0x700|channel.error;goto reject;}
        ADD(sub.tstates,sub.fetches);
        emit(output,sink,context,channel.writes,channel.count);
        if(channel.unwind==2) return 1;
    }
    ADD(10,1);return 1;
reject:
    work->tstates=work->fetches=0;return 0;
}

static void capture(void *context,const u8 *writes,u16 count)
{
    SourceAudioReaderOutput *output=(SourceAudioReaderOutput *)context;u16 n;
    for(n=0;n<count;n++) output->writes[output->count++]=writes[n];
}

u8 source_audio_reader(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                       u16 *de,SourceClockWork *work,SourceAudioReaderOutput *output)
{
    u8 old[400],accepted;u16 original_de=*de;SourceAudioReaderStatus status;
    copy_state(old,state);output->count=0;
    accepted=source_audio_reader_stream(state,low,low_bytes,bank,de,work,&status,capture,output);
    output->error=status.error;output->track=status.track;
    if(!accepted)
    {copy_state(state,old);*de=original_de;output->count=output->track=0;}
    return accepted;
}
