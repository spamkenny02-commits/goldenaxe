/* Compile a separately named composition from the authoritative semantic
 * modules. Default gameplay keeps its existing channel rollback/calendar;
 * the clocked loader can avoid nested copies while counting identical T/M1.
 * Each channel's PSG list is emitted only after that channel succeeds. */
#define GAW_AUDIO_STREAM_CHANNELS
#define source_audio_reader source_audio_reader_fast
#define source_audio_reader_stream source_audio_reader_stream_fast
#define source_audio_tone source_audio_tone_fast
#define source_audio_noise source_audio_noise_fast
#define source_audio_sequence source_audio_sequence_fast
#define source_audio_noise_sequence source_audio_noise_sequence_fast
#define source_audio_noise_note source_audio_noise_note_fast
#define copy_state fast_tone_copy_state
#include "source_audio_tone.c"
#undef copy_state
#define copy_state fast_noise_copy_state
#include "source_audio_noise.c"
#undef copy_state
#define copy_state fast_sequence_copy_state
#include "source_audio_sequence.c"
#undef copy_state
#define copy_state fast_reader_copy_state
#include "source_audio_reader.c"
