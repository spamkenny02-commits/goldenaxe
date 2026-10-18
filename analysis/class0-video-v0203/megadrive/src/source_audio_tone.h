#ifndef GAW_SOURCE_AUDIO_TONE_H
#define GAW_SOURCE_AUDIO_TONE_H
#include "source_audio_sequence.h"
/* Original84C7, including note/release, modulation and envelope composition.
 * Component returns consume inner stack unwinds; no whole-reader unwind.
 * Failed reads/control bounds restore all400 bytes and DE, with no PSG writes. */
u8 source_audio_tone(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                     const u8 *bank6,u16 *de,SourceClockWork *work,
                     SourceAudioSequenceOutput *output);
#endif
