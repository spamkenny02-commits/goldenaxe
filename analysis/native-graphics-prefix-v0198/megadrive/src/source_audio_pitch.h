#ifndef GAW_SOURCE_AUDIO_PITCH_H
#define GAW_SOURCE_AUDIO_PITCH_H
#include "source_clock.h"
typedef struct {u16 hl;u8 unwind;} SourceAudioPitchOutput;
/* Original82C5: delayed vibrato, signed16-bit delta, eight pitch tables and
 * source caller unwind. Failed reads/control loops reject without mutation. */
u8 source_audio_pitch(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                      const u8 *bank6,u16 return_address,u16 *de,
                      SourceClockWork *work,SourceAudioPitchOutput *output);
#endif
