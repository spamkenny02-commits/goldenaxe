#ifndef GAW_SOURCE_AUDIO_DISPATCH_H
#define GAW_SOURCE_AUDIO_DISPATCH_H
#include "source_audio_prefix.h"

/* PSG side effects emitted by original 80FF; mute means the 8412 table.
 * Keeping writes explicit lets the same semantic code run in clock oracles. */
typedef struct { u8 mute,count,writes[4]; } SourceAudioDispatchOutput;
/* Returns zero without mutation for commands whose ROM paths are unaudited. */
u8 source_audio_dispatch(u8 *state,const u8 *bank6,SourceClockWork *work,
                         SourceAudioDispatchOutput *output);
#endif
