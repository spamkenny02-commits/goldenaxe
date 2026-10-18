#include "source_audio_timed.h"

u8 source_audio_noise_note_timed(u8 *state,u16 offset,u8 note,u32 source_entry,
                                SourceClockWork *work,SourcePsgEvent *event,u8 *has_event)
{
    SourceAudioSequenceOutput output;
    if(work) work->tstates=work->fetches=0;
    if(has_event) *has_event=0;
    if(!state || !work || !event || !has_event) return 0;
    if(!source_audio_noise_note(state,offset,note,work,&output)) return 0;
    if(output.count)
    {
        event->due=source_entry+(work->tstates-10)*15;
        event->value=output.writes[0];*has_event=1;
    }
    return 1;
}

u8 source_audio_envelope_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                              const u8 *bank,u16 *de,u32 source_entry,SourceClockWork *work,
                              SourceAudioEnvelopeOutput *output,SourcePsgEvent *event)
{
    if(work) work->tstates=work->fetches=0;
    if(output) output->accumulator=output->unwind=output->write=output->psg=0;
    if(!state || !low || !bank || !de || !work || !output || !event) return 0;
    if(!source_audio_envelope(state,offset,low,low_bytes,bank,de,work,output)) return 0;
    if(output->write)
    {
        event->due=source_entry+(work->tstates-10)*15;
        event->value=output->psg;
    }
    return 1;
}
