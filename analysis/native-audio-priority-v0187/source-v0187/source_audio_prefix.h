#ifndef GAW_SOURCE_AUDIO_PREFIX_H
#define GAW_SOURCE_AUDIO_PREFIX_H
#include "source_clock.h"

#define SOURCE_AUDIO_BYTES 400
/* Semantic state and original Z80 work; no CPU interpretation or PSG writes.
 * A complete reader still needs dispatch, priority effects and channels. */
u8 source_audio_gate(u8 *state,SourceClockWork *work);
void source_audio_arbitrate(u8 *state,const u8 *bank6,SourceClockWork *work);
void source_audio_tempo(u8 *state,SourceClockWork *work);
void source_audio_stop(u8 *state,SourceClockWork *work);
void source_audio_fade(u8 *state,SourceClockWork *work);

#endif
