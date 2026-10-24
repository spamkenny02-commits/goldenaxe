#ifndef GAW_SOURCE_IRQ_VIDEO_H
#define GAW_SOURCE_IRQ_VIDEO_H
#include "source_room_memory.h"
typedef struct {
 const u8 *rom,*sram; /* Original256KiB ROM; optional16KiB mapped cartridge RAM. */
 u8 *vram,*cram,*registers; /*16KiB,32 bytes,16 registers. */
 u32 bytes;u16 tiles,error;
} SourceIrqVideo;
enum {SOURCE_IRQ_VIDEO_INVALID=0xb00,SOURCE_IRQ_VIDEO_READ,SOURCE_IRQ_VIDEO_QUEUE};
/* Full IRQ video stages, before native audio. Reads live source RAM, never
 * commits IRQ RAM (the canonical adapter owns that). Queue self-modification
 * is staged in a private compact view, including its terminator and heights.
 * Mirrors can be partly published on failure: stop session, never retry.
 * This is byte delivery, not physical MD scheduling or active-display timing. */
u8 source_irq_video_publish(void *user,const SourceIrqContext *context,
 const SourceClockIrq *entry,u16 *tile_count);
#endif
