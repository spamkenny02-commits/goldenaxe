#ifndef GAW_MD_Z80_VIDEO_DMA_H
#define GAW_MD_Z80_VIDEO_DMA_H
#include "md_z80_psg.h"
/* Experimental single32byte tile transfer. H32/224 with DMA enabled by
 * SGDK initialization, masked native IRQs,
 * one VDP/bus owner, intact PSG timer with gaps<5lines. Uses only a subset
 * of VBlank (rawV235..252) and a stable even stamp at most2raw lines old.
 * This window excludes the six-line NTSC duplicate V-counter range.
 * Rechecks stamp/grant/beam after BUSREQ, then issues a precomputed DMA.
 * Caller owns valid word-aligned DMA-readable source and target tile.
 * The32byte source must not cross a128KiB DMA bank boundary.
 * WAIT does not upload; caller retains/retries the job without dropping it.
 * Auto-increment is set to2 through SGDK even when returning WAIT.
 * This primitive alone provides no frame deadline or renderer queue. */
u8 md_z80_video_dma_try(MdZ80PsgMailbox *mailbox,const u32 *source,u16 tile);
/* Caller-owned RAM token, immutable after successful prepare until commit.
 * Keep source bytes intact across WAIT. Job/source must be disjoint and
 * H32/224 DMA mode must remain unchanged. prepare is atomic on INVALID and
 * does not touch hardware; try_prepared retains the job on WAIT/FAULT and
 * consumes it on OK. Auto-increment may become2 on a rejected bus attempt.
 * Same masked-IRQ/single-owner/timer/window contract as the direct API.
 * The prepared path uses only the atomic8bit V stamp, not the multi-byte
 * counter or its seqlock. It rechecks ready/grant and V age under BUSACK;
 * odd counter publication alone does not reject a video transfer. */
typedef struct {
    u16 source_low,source_mid,source_high,ready;
    volatile u32 command;
} MdZ80VideoDmaJob;
u8 md_z80_video_dma_prepare(MdZ80VideoDmaJob *job,const u32 *source,u16 tile);
u8 md_z80_video_dma_try_prepared(MdZ80PsgMailbox *mailbox,MdZ80VideoDmaJob *job);
#endif
