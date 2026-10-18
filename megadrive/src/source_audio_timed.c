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
