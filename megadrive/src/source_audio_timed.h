#ifndef GAW_SOURCE_AUDIO_TIMED_H
#define GAW_SOURCE_AUDIO_TIMED_H
#include "source_audio_sequence.h"
#include "source_audio_envelope.h"
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
/* Original854B envelope, preserving its accumulator/DE/unwind interface.
 * An optional mute OUT is immediately followed by RET at864E. Its event is
 * therefore at source_entry+(helperT-10)*15, including the table-unwind POP.
 * All pointer arguments are required. On failure valid work/output are zero;
 * on failure or output->write==0 event stays untouched. Queue retry rules
 * are the same as for the noise selector above. */
u8 source_audio_envelope_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                              const u8 *bank,u16 *de,u32 source_entry,SourceClockWork *work,
                              SourceAudioEnvelopeOutput *output,SourcePsgEvent *event);
/* Per-byte completed-OUT times in Z80 T states relative to helper entry.
 * Same bounded semantics/rollback and unsupported controls as8357/8655.
 * On failure count is zero; prior timestamp slots are not valid events.
 * These lists are caller-owned and do not publish or pace PSG writes. */
typedef struct {
    u16 de,count;u8 unwind,error,writes[512];u32 write_tstates[512];
} SourceAudioTimedSequenceOutput;
u8 source_audio_sequence_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                               const u8 *bank,SourceClockWork *work,SourceAudioTimedSequenceOutput *output);
u8 source_audio_noise_sequence_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                                     const u8 *bank,SourceClockWork *work,SourceAudioTimedSequenceOutput *output);
#endif
