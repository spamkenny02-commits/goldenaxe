#ifndef GAW_SOURCE_AUDIO_SEQUENCE_H
#define GAW_SOURCE_AUDIO_SEQUENCE_H
#include "source_clock.h"
/* At most two PSG writes per control, and256 controls per bounded invocation.
 * No PSG output is applied until the semantic transaction succeeds. */
typedef struct {u16 de,count;u8 unwind,error,writes[512];} SourceAudioSequenceOutput;
/* Original8357 tonal sequences, deterministic controls and8211 restoration.
 * E3/EC/EF/FE/FF remain explicit unsupported paths pending their R/context audit. */
u8 source_audio_sequence(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                         const u8 *bank6,SourceClockWork *work,SourceAudioSequenceOutput *output);
/* Noise864F note boundary after DEC/JP; unwind2 exits the complete8000 reader. */
u8 source_audio_noise_sequence(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                               const u8 *bank6,SourceClockWork *work,SourceAudioSequenceOutput *output);
/* Original8679 selector; DE is unchanged. */
u8 source_audio_noise_note(u8 *state,u16 offset,u8 note,SourceClockWork *work,SourceAudioSequenceOutput *output);
#endif
