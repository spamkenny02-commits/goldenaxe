/* Reuse84C7 semantics with event sidecars. Sequence events start after the
 *47T DEC/JR/CALL prefix; the two frequency OUTs are42T apart. */
#include "source_audio_timed.h"
#include "source_audio_tone.h"
#define GAW_AUDIO_TIMED_TONE
#define GAW_AUDIO_TIMED_STAMP(o,t) ((o)->write_tstates[(o)->count]=(t))
#define SourceAudioSequenceOutput SourceAudioTimedSequenceOutput
#define source_audio_tone source_audio_tone_timed
#define source_audio_sequence source_audio_sequence_timed
#include "source_audio_tone.c"
