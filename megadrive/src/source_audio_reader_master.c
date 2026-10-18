/* Fuse helper->reader and reader->master rebasing in one pass. Channel
 * semantics and fast failed-channel state behavior remain authoritative. */
#include "source_audio_timed.h"
u8 source_audio_tone_fast_timed(u8 *,u16,const u8 *,u16,const u8 *,u16 *,SourceClockWork *,SourceAudioTimedSequenceOutput *);
u8 source_audio_noise_fast_timed(u8 *,u16,const u8 *,u16,const u8 *,u16 *,SourceClockWork *,SourceAudioTimedSequenceOutput *);
typedef struct {u32 epoch;void *user;} MasterEpoch;
#define GAW_AUDIO_EMIT_TIMES(times,count,base,context) do { \
    u16 n;u32 epoch=((MasterEpoch *)context)->epoch; \
    for(n=0;n<count;n++) times[n]=epoch+(base+times[n])*15; \
} while(0)
#define GAW_AUDIO_EMIT_CONTEXT(context) (((MasterEpoch *)context)->user)
#define source_audio_tone_timed source_audio_tone_fast_timed
#define source_audio_noise_timed source_audio_noise_fast_timed
#define source_audio_reader_stream_timed reader_master_inner
#include "source_audio_reader_timed.c"

u8 source_audio_reader_stream_fast_master(u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                                         u16 *de,SourceClockWork *work,SourceAudioReaderStatus *status,
                                         u32 epoch,SourceAudioTimedReaderSink sink,void *context)
{
    MasterEpoch clock;clock.epoch=epoch;clock.user=context;
    return reader_master_inner(state,low,low_bytes,bank,de,work,status,sink,&clock);
}
