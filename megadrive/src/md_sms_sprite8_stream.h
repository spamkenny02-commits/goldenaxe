#ifndef GAW_MD_SMS_SPRITE8_STREAM_H
#define GAW_MD_SMS_SPRITE8_STREAM_H
#include <genesis.h>
#include "source_sms_sprite8.h"
#include "md_z80_video_span.h"
/* One masked-IRQ H32/224 VDP owner,display disabled through done. Caller
 * reserves64 clone tiles and keeps512tile pattern shadow immutable. State
 * must be zero-initialized first. SAT/payload are owned across WAIT. This
 * module publishes no IRQ/status latency and never enables the display. */
typedef struct {
    SourceSmsSprite8 frame;
    MdZ80VideoSpan job;
    u32 payload[32];
    const u32 *patterns;
    u16 sprite_cursor,sat_cursor,sat_address,address,count;
    u8 ready,done,error,verify,kind,last_kind;
    u32 readback_words,readback_errors;
} MdSmsSprite8Stream;
u8 md_sms_sprite8_stream_begin(MdSmsSprite8Stream *state,const u8 *sat,const u32 *patterns,
                               u8 reg0,u8 reg1,u8 reg6,u16 tile_base,u8 verify);
/* OK consumes exactly one1..4tile span. Four final spans overwrite all64
 * MD SAT entries, clearing old tails even for an empty source list. */
u8 md_sms_sprite8_stream_step(MdSmsSprite8Stream *state,MdZ80PsgMailbox *mailbox);
#endif
