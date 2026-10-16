#ifndef GAW_SOURCE_AUDIO_ENVELOPE_H
#define GAW_SOURCE_AUDIO_ENVELOPE_H
#include "source_clock.h"
typedef struct { u8 accumulator,unwind,write,psg; } SourceAudioEnvelopeOutput;
/* Original854B ADSR and table envelopes. Table control83 reads through DE,
 * not the envelope stream. Failed reads/loops reject without state mutation. */
u8 source_audio_envelope(u8 *state,u16 offset,const u8 *low,u16 low_bytes,
                         const u8 *bank6,u16 *de,SourceClockWork *work,
                         SourceAudioEnvelopeOutput *output);
#endif
