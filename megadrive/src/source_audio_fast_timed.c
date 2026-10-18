/* Fast timed composition reuses the same annotated semantic C. Only nested
 * rollback copies are omitted; successful state/work/events are identical. */
#include "source_audio_timed.h"
#include "source_audio_tone.h"
#include "source_audio_noise.h"
u8 source_audio_sequence_fast_timed(u8 *,u16,const u8 *,u16,const u8 *,SourceClockWork *,SourceAudioTimedSequenceOutput *);
u8 source_audio_noise_sequence_fast_timed(u8 *,u16,const u8 *,u16,const u8 *,SourceClockWork *,SourceAudioTimedSequenceOutput *);
#define GAW_AUDIO_STREAM_CHANNELS
#define GAW_AUDIO_TIMED_STAMP(o,t) ((o)->write_tstates[(o)->count]=(t))
#define SourceAudioSequenceOutput SourceAudioTimedSequenceOutput
#define source_audio_tone source_audio_tone_fast_timed
#define source_audio_noise source_audio_noise_fast_timed
#define source_audio_sequence source_audio_sequence_fast_timed
#define source_audio_noise_sequence source_audio_noise_sequence_fast_timed
#define source_audio_noise_note gaw_audio_fast_timed_noise_note_relative
#define GAW_AUDIO_TIMED_TONE
#include "source_audio_tone.c"
#undef GAW_AUDIO_TIMED_TONE
#define GAW_AUDIO_TIMED_NOISE
#include "source_audio_noise.c"
#undef GAW_AUDIO_TIMED_NOISE
#define GAW_AUDIO_TIMED_SEQUENCE
#include "source_audio_sequence.c"
#define source_audio_tone_timed source_audio_tone_fast_timed
#define source_audio_noise_timed source_audio_noise_fast_timed
#define source_audio_reader_stream_timed source_audio_reader_stream_fast_timed
#include "source_audio_reader_timed.c"
