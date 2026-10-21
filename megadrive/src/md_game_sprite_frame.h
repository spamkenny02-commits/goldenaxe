#ifndef GAW_MD_GAME_SPRITE_FRAME_H
#define GAW_MD_GAME_SPRITE_FRAME_H
#include "source_game_irq.h"
#include "md_sms_sprite8_stream.h"
/* One foreground owner, masked native IRQs, H32/224 and hidden display.
 * Zero-init before first bind. Pattern shadow is immutable while pending.
 * The source IRQ sink only owns a copy: no VDP work inside logical IRQ.
 * Drain one packet completely before another full IRQ; rejection is fatal,
 * never a license to drop/replace source frames. Source dates are retained,
 * not an assertion of physical delivery at those dates. */
typedef struct {
 MdSmsSprite8Stream stream;
 SourceGameSatPacket packet;
 const u32 *patterns;
 u32 accepted,delivered;
 u16 tile_base;
 u8 reg0,reg1,reg6,verify,ready,pending,error;
} MdGameSpriteFrame;
u8 md_game_sprite_frame_bind(MdGameSpriteFrame *state,const u32 *patterns,
 u8 reg0,u8 reg1,u8 reg6,u16 tile_base,u8 verify);
/* SourceGameSatSink:1 accepts,0 fails. Caller aborts on failure. */
u8 md_game_sprite_frame_capture(void *state,const SourceGameSatPacket *packet);
/* MD_Z80_PSG_OK consumes one bounded DMA job. WAIT retains owned data.
 * A completed packet clears pending and increments delivered. */
u8 md_game_sprite_frame_step(MdGameSpriteFrame *state,MdZ80PsgMailbox *mailbox);
#endif
