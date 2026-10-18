#include "source_audio_timed.h"
static void prefix_rebase(SourceAudioTimedDispatchOutput *output,u32 base)
{u16 n;for(n=0;n<output->count;n++) output->write_tstates[n]+=base;}
static void prefix_mute(SourceAudioTimedDispatchOutput *output,u32 first)
{u16 n;for(n=0;n<10;n++) output->mute_tstates[n]=first+(u32)n*21;}
#define GAW_AUDIO_PREFIX_STAMP(o,t) ((o)->write_tstates[(o)->count]=(t))
#define GAW_AUDIO_PREFIX_REBASE(o,t) prefix_rebase(o,t)
#define GAW_AUDIO_PREFIX_MUTE(o,t) prefix_mute(o,t)
#define SourceAudioDispatchOutput SourceAudioTimedDispatchOutput
#define source_audio_dispatch source_audio_dispatch_timed
#define source_audio_priority source_audio_priority_timed
#define source_audio_restore source_audio_restore_timed
#include "source_audio_dispatch.c"
#include "source_audio_priority.c"

u8 source_audio_gate_timed(u8 *state,SourceClockWork *work,SourceAudioTimedDispatchOutput *output)
{
    u8 gate=state[10],accepted;output->mute=output->count=0;
    accepted=source_audio_gate(state,work);
    if(gate&128) {output->mute=1;prefix_mute(output,work->tstates-249);}
    return accepted;
}
void source_audio_fade_timed(u8 *state,SourceClockWork *work,SourceAudioTimedDispatchOutput *output)
{
    u8 stopping=state[11]==1 && state[12]==1;output->mute=output->count=0;
    source_audio_fade(state,work);
    if(stopping) {output->mute=1;prefix_mute(output,work->tstates-249);}
}
