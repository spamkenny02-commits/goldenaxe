#ifndef GAW_SOURCE_AUDIO_TIMED_H
#define GAW_SOURCE_AUDIO_TIMED_H
#include "source_audio_sequence.h"
#include "source_psg_queue.h"

/* Original8679 noise selection, with its optional PSG event timestamp.
 * source_entry is the8679 entry time in source master ticks (15 per Z80 T).
 * OUT precedes the final10T RET on both writing exits; suppressed output has
 * no event. Reuses the authoritative state/work model, without PSG port IO.
 * All pointers are required. Failure zeroes valid work/has_event outputs;
 * event is unchanged on failure or suppression. State changes on success.
 * Keep the returned event when enqueueing hits FULL; retry publication, not
 * semantic execution. This is one helper, not a timed complete8000 reader. */
u8 source_audio_noise_note_timed(u8 *state,u16 offset,u8 note,u32 source_entry,
                                SourceClockWork *work,SourcePsgEvent *event,u8 *has_event);
#endif
