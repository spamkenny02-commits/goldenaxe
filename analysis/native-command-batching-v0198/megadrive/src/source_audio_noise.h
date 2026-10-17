#ifndef GAW_SOURCE_AUDIO_NOISE_H
#define GAW_SOURCE_AUDIO_NOISE_H
#include "source_audio_sequence.h"
/* Full864F channel: held envelope or new sequence. unwind2 returns from
 * the entire8000 reader, not merely this channel. DE andwork are explicit. */
u8 source_audio_noise(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                      const u8 *bank6,u16 *de,SourceClockWork *work,SourceAudioSequenceOutput *output);
#endif
