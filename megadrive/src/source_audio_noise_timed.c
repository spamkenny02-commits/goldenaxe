/* Timed864F composition: preserve the ordinary state/work/rollback model,
 * rebase sequence events by the33T entry prefix, and timestamp volume OUTs. */
#include "source_audio_timed.h"
#include "source_audio_noise.h"
#define GAW_AUDIO_TIMED_NOISE
#define GAW_AUDIO_TIMED_STAMP(o,t) ((o)->write_tstates[(o)->count]=(t))
#define SourceAudioSequenceOutput SourceAudioTimedSequenceOutput
#define source_audio_noise source_audio_noise_timed
#define source_audio_noise_sequence source_audio_noise_sequence_timed
#include "source_audio_noise.c"
