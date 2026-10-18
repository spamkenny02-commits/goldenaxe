#ifndef GAW_SOURCE_AUDIO_FAST_H
#define GAW_SOURCE_AUDIO_FAST_H
#include "source_audio_reader.h"
/* Clocked composition uses the same semantic channel/sequence code without
 * nested channel snapshots. The capture reader still owns full rollback.
 * Streaming rejection can leave state changed, including the failed channel;
 * its writes are discarded, but already emitted channel writes remain. */
u8 source_audio_reader_fast(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank6,
                            u16 *de,SourceClockWork *work,SourceAudioReaderOutput *output);
u8 source_audio_reader_stream_fast(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank6,
                                   u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                                   SourceAudioReaderSink sink,void *context);
#endif
