#ifndef GAW_SOURCE_AUDIO_READER_H
#define GAW_SOURCE_AUDIO_READER_H
#include "source_clock.h"
/* Seven bounded channel lists plus prefix mute/dispatch/priority effects. */
#define SOURCE_AUDIO_READER_WRITES (7*512+32)
typedef struct {
    u16 count,error;
    u8 track,writes[SOURCE_AUDIO_READER_WRITES];
} SourceAudioReaderOutput;
typedef struct {u16 count,error;u8 track;} SourceAudioReaderStatus;
typedef void (*SourceAudioReaderSink)(void *context,const u8 *writes,u16 count);
/* Production path: emit each successful prefix/channel immediately. Earlier
 * writes/state remain published if a later unsupported path is rejected. */
u8 source_audio_reader_stream(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank6,
                              u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                              SourceAudioReaderSink sink,void *context);
/* Original8000, including gate, all prefixes, compensation and seven slots.
 * Work excludes the calling CALL instruction. Unsupported paths roll back
 * all400 bytes and DE. This capture API retains writes for the caller; the
 * playable ROM uses the streaming API to avoid a large global RAM buffer. */
u8 source_audio_reader(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank6,
                       u16 *de,SourceClockWork *work,SourceAudioReaderOutput *output);
#endif
