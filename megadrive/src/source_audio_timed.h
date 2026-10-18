#ifndef GAW_SOURCE_AUDIO_TIMED_H
#define GAW_SOURCE_AUDIO_TIMED_H
#include "source_audio_sequence.h"
#include "source_audio_envelope.h"
#include "source_audio_dispatch.h"
#include "source_audio_priority.h"
#include "source_audio_reader.h"
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
/* Complete864F noise channel; list times are relative to864F entry. */
u8 source_audio_noise_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                           const u8 *bank,u16 *de,SourceClockWork *work,SourceAudioTimedSequenceOutput *output);
/* Complete84C7 tonal channel; list times are relative to84C7 entry. */
u8 source_audio_tone_timed(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                          const u8 *bank,u16 *de,SourceClockWork *work,SourceAudioTimedSequenceOutput *output);
/* Prefix sidecars retain the ordinary mute/count interface. When mute is
 * set, the ten8412 table bytes use mute_tstates; ordinary writes use their
 * own sidecar. All times are relative to the corresponding helper entry. */
typedef struct {u8 mute,count,writes[4];u32 write_tstates[4],mute_tstates[10];} SourceAudioTimedDispatchOutput;
u8 source_audio_dispatch_timed(u8 *state,const u8 *bank,SourceClockWork *work,SourceAudioTimedDispatchOutput *output);
u8 source_audio_priority_timed(u8 *state,const u8 *bank,u16 *de,SourceClockWork *work,SourceAudioTimedDispatchOutput *output);
u8 source_audio_restore_timed(u8 *state,const u8 *bank,u8 command,u16 *de,SourceClockWork *work,SourceAudioTimedDispatchOutput *output);
u8 source_audio_gate_timed(u8 *state,SourceClockWork *work,SourceAudioTimedDispatchOutput *output);
void source_audio_fade_timed(u8 *state,SourceClockWork *work,SourceAudioTimedDispatchOutput *output);
/* Streaming8000 composition. Emits successful prefix/channel lists with
 * per-byte completed-OUT offsets in Z80 T states from8000 entry. Earlier
 * lists remain published on a later failure, as in the ordinary stream API.
 * Sink must copy any retained data before returning; buffers are temporary. */
typedef void (*SourceAudioTimedReaderSink)(void *context,const u8 *writes,const u32 *tstates,u16 count);
u8 source_audio_reader_stream_timed(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                                    u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                                    SourceAudioTimedReaderSink sink,void *context);
/* Same successful timed lists without nested channel/sequence snapshots.
 * Rejection may leave the failed channel's state changed, matching the fast
 * untimed stream contract; its writes remain discarded. Earlier successful
 * lists/state are retained. This is not an outer transactional capture API. */
u8 source_audio_reader_stream_fast_timed(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                                         u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                                         SourceAudioTimedReaderSink sink,void *context);
/* Diagnostic variant (measured slower in loading; not production-selected).
 * Same fast stream, directly emitting modulo32-bit master dates at15 master
 * ticks per source T, relative to the supplied8000-entry epoch. The existing
 * sink type is reused but its time array is in MASTER TICKS for this API.
 * Temporary arrays still require synchronous copying; sink must be nonnull. */
u8 source_audio_reader_stream_fast_master(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                                         u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                                         u32 epoch,SourceAudioTimedReaderSink sink,void *context);
#endif
