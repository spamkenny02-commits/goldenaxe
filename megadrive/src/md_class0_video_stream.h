#ifndef GAW_MD_CLASS0_VIDEO_STREAM_H
#define GAW_MD_CLASS0_VIDEO_STREAM_H
#include <genesis.h>
#include "md_z80_video_span.h"
/* One masked-IRQ VDP owner, H32/224, BG_A64x32. Resident patterns and
 * backdrop belong to the caller. Publish at1706/1deb/24bf respectively.
 * Zero-initialize state before first begin. State, map, palette and payload
 * remain owned until done; keep mode/plane layout fixed. No deadlines. */
typedef struct {
    MdZ80VideoSpan job;
    u32 payload[32];
    u16 map[768],palette[32];
    u16 pattern_cursor,map_row,address,count;
    u8 ready,kind,last_kind,error,verify,done,hidden;
    u32 readback_words,readback_errors;
} MdClass0VideoStream;
u8 md_class0_video_stream_begin(MdClass0VideoStream *state,u8 verify);
/* Caller keeps display off until done; this mode never enables it. */
u8 md_class0_video_stream_begin_hidden(MdClass0VideoStream *state,u8 verify);
u8 md_class0_video_stream_map(MdClass0VideoStream *state,const u8 *sms);
u8 md_class0_video_stream_palette(MdClass0VideoStream *state,const u8 *upper);
/* OK means exactly one pattern span/map row/palette committed; WAIT retains
 * pending data. A subsequent call after done returns WAIT. Fault is sticky. */
u8 md_class0_video_stream_step(MdClass0VideoStream *state,MdZ80PsgMailbox *mailbox);
#endif
