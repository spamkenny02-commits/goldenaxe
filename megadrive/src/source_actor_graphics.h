#ifndef GAW_SOURCE_ACTOR_GRAPHICS_H
#define GAW_SOURCE_ACTOR_GRAPHICS_H
#include "source_graphics_load.h"
typedef struct {
 u8 *actors;      /* C600..C8FF */
 u8 *patterns;    /* full16384-byte SMS VRAM mirror */
 u8 *terrain;     /* D100..D4FF; remap changes its first112 bytes */
 u8 *allocated;   /* C067, not in compact IRQ RAM */
} SourceActorGraphicsData;
/* Original1D0D including RET. Valid original palette remap and whole tiles.
 * patterns points at the range, address is its logical VDP command address.
 * terrain aliases D100..D4FF. Commit bytes at source instruction boundaries.
 * Mirrors logical VRAM only; physical MD upload/pacing remains external. */
u8 source_actor_remap(SourceClock *clock,SourceIrqContext *context,
 u8 *patterns,u8 *terrain,u16 address,u16 bytes,u8 remap);
/* Original1853..18E1, excluding RET. rom is the original immutable256KiB
 * image, data contains a valid original room list after1780 preparation.
 * Reuses duplicate types; otherwise decodes original RLE and palette remap.
 * Shares clock/IRQ/audio with preceding loading. Stop on partial failure. */
u8 source_actor_graphics(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceActorGraphicsData *data,
 SourceGraphicsCheckpoint checkpoint,void *user);
#endif
