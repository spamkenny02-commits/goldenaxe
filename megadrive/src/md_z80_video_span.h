#ifndef GAW_MD_Z80_VIDEO_SPAN_H
#define GAW_MD_Z80_VIDEO_SPAN_H
#include "md_z80_psg.h"
/* Experimental contiguous1..4tile DMA. Caller owns a disjoint, immutable
 * RAM token and word-aligned readable payload until OK; WAIT/FAULT retain
 * both. H32/224, DMA enabled, masked native IRQs and one bus/VDP owner.
 * Source may not cross a128KiB DMA bank; destination may not wrap VRAM.
 * Only atomic V is read, never the multi-byte counter. Held-bus grant,
 * ready/error and V235..252 are rechecked. Age<=1line for2..4tiles,
 * <=2lines for1tile. The independent Z80 sample gap must remain<5lines.
 * No renderer queue, source lifetime management or frame deadline provided.
 * prepare is atomic on INVALID and touches no hardware. step may set the
 * SDK auto-increment to2 even on WAIT; OK consumes the token. */
typedef struct {
    u16 source_low,source_mid,source_high,length_low,ready;
    volatile u32 command;
} MdZ80VideoSpan;
u8 md_z80_video_span_prepare(MdZ80VideoSpan *job,const u32 *source,u16 tile,u16 count);
u8 md_z80_video_span_try(MdZ80PsgMailbox *mailbox,MdZ80VideoSpan *job);
/* Optional early-window path requires the refresh driver capability in
 * ready (mask2). Unsupported ready profiles return INVALID. It uses only
 * V224..228 and235..252 (235..251 for the fresh-grant profile),
 * excludes raw229..234,
 * and must complete within
 * three lines after its held-bus beam read for up to8tiles (two lines
 * for up to4). The refresh constructor creates a distinct token that the
 * legacy try API rejects; its count range is1..8. Spans above4 require
 * the fresh-grant driver capability (mask4), no pending PSG descriptors,
 * and a granted V stamp in the same raw scanline (age0). Other span contracts still apply. */
#define MD_Z80_VIDEO_SPAN_REFRESH_CAP 2
#define MD_Z80_VIDEO_SPAN_GRANT_CAP 4
u8 md_z80_video_span_prepare_refresh(MdZ80VideoSpan *job,const u32 *source,u16 tile,u16 count);
u8 md_z80_video_span_try_refresh(MdZ80PsgMailbox *mailbox,MdZ80VideoSpan *job);
#endif
