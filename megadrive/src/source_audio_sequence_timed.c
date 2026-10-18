/* Recompile the authoritative sequence semantics with an additional sidecar
 * for completed-OUT times. The ordinary production composition has no sidecar
 * stores, larger output objects or extra timing arithmetic. */
#include "source_audio_timed.h"
#define GAW_AUDIO_TIMED_SEQUENCE
#define GAW_AUDIO_TIMED_STAMP(o,t) ((o)->write_tstates[(o)->count]=(t))
#define SourceAudioSequenceOutput SourceAudioTimedSequenceOutput
#define source_audio_sequence source_audio_sequence_timed
#define source_audio_noise_sequence source_audio_noise_sequence_timed
#define source_audio_noise_note gaw_audio_timed_noise_note_relative
#include "source_audio_sequence.c"
