#include "source_audio_timed.h"
#define ADD(t,m) do {work->tstates+=(t);work->fetches+=(m);} while(0)
#ifndef GAW_AUDIO_EMIT_TIMES
#define GAW_AUDIO_EMIT_TIMES(times,count,base,context) do {u16 n;for(n=0;n<count;n++) times[n]+=base;} while(0)
#endif
#ifndef GAW_AUDIO_EMIT_CONTEXT
#define GAW_AUDIO_EMIT_CONTEXT(context) (context)
#endif
static void emit(SourceAudioReaderStatus *status,SourceAudioTimedReaderSink sink,void *context,
                 const u8 *writes,u32 *times,u16 count,u32 base)
{
    if(!count) return;
    GAW_AUDIO_EMIT_TIMES(times,count,base,context);
    sink(GAW_AUDIO_EMIT_CONTEXT(context),writes,times,count);status->count+=count;
}
static void prefix(SourceAudioReaderStatus *status,SourceAudioTimedReaderSink sink,void *context,
                   const u8 *bank,SourceAudioTimedDispatchOutput *output,u32 base)
{
    if(output->mute) emit(status,sink,context,bank+0x412,output->mute_tstates,10,base);
    emit(status,sink,context,output->writes,output->write_tstates,output->count,base);
}
u8 source_audio_reader_stream_timed(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                                    u16 *de,SourceClockWork *work,SourceAudioReaderStatus *output,
                                    SourceAudioTimedReaderSink sink,void *context)
{
    u8 phase;u16 offset;u32 base;SourceClockWork sub;
    SourceAudioTimedDispatchOutput dispatch;SourceAudioTimedSequenceOutput channel;
    output->count=output->error=output->track=0;
    if(source_audio_gate_timed(state,work,&dispatch))
    {prefix(output,sink,context,bank,&dispatch,0);return 1;}
    source_audio_arbitrate(state,bank,&sub);ADD(17+sub.tstates,1+sub.fetches);
    source_audio_tempo(state,&sub);ADD(17+sub.tstates,1+sub.fetches);
    base=work->tstates+17;source_audio_fade_timed(state,&sub,&dispatch);ADD(17+sub.tstates,1+sub.fetches);
    prefix(output,sink,context,bank,&dispatch,base);phase=state[5];base=work->tstates+17;
    if(!source_audio_dispatch_timed(state,bank,&sub,&dispatch)) {output->error=0x100|phase;goto reject;}
    ADD(17+sub.tstates,1+sub.fetches);if(phase>=0x81 && phase<=0x8d) output->track=phase;
    prefix(output,sink,context,bank,&dispatch,base);base=work->tstates+17;
    if(!source_audio_priority_timed(state,bank,de,&sub,&dispatch)) {output->error=0x200|state[9];goto reject;}
    ADD(17+sub.tstates,1+sub.fetches);prefix(output,sink,context,bank,&dispatch,base);ADD(27,3);
    if(state[3])
    {
        ADD(24,3);phase=(u8)(state[4]+1);
        if(phase<6) ADD(12,1);else {ADD(11,2);phase=0;}
        state[4]=phase;ADD(17,2);if(!phase) {ADD(11,1);return 1;}ADD(5,1);
    }
    for(offset=0x40;offset<=0x160;offset+=0x30)
    {
        ADD(34,4);if(!(state[offset]&128)) {ADD(10,1);continue;}
        ADD(17,1);base=work->tstates;
        if(offset==0xd0)
        {
            if(!source_audio_noise_timed(state,offset,low,low_bytes,bank,de,&sub,&channel))
            {output->error=0x600|channel.error;goto reject;}
        }
        else if(!source_audio_tone_timed(state,offset,low,low_bytes,bank,de,&sub,&channel))
        {output->error=0x700|channel.error;goto reject;}
        ADD(sub.tstates,sub.fetches);emit(output,sink,context,channel.writes,channel.write_tstates,channel.count,base);
        if(channel.unwind==2) return 1;
    }
    ADD(10,1);return 1;
reject:
    work->tstates=work->fetches=0;return 0;
}
