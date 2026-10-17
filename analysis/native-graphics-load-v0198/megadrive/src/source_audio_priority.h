#ifndef GAW_SOURCE_AUDIO_PRIORITY_H
#define GAW_SOURCE_AUDIO_PRIORITY_H
#include "source_audio_dispatch.h"
/* Original81F8 queue and8211 restoration. DE is retained where the Z80
 * path leaves it untouched; PSG writes are returned explicitly. */
u8 source_audio_priority(u8 *state,const u8 *bank6,u16 *de,SourceClockWork *work,
                        SourceAudioDispatchOutput *output);
u8 source_audio_restore(u8 *state,const u8 *bank6,u8 command,u16 *de,
                       SourceClockWork *work,SourceAudioDispatchOutput *output);
#endif
