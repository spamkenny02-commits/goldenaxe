#ifndef GAW_SOURCE_HERO_INITIALIZE_H
#define GAW_SOURCE_HERO_INITIALIZE_H
#include "source_graphics_load.h"
#include "source_room_memory.h"
/* Original2C63 and callees, including RET and prefetched24E7. Full RAM body
 * is ctx->full_ram; compact IRQ/audio pages are live through accessors.
 * Valid source class0..2, item0..16, direction0..3. ROM is immutable.
 * Initialization only, not hero physics. Keep completed effects on failure. */
u8 source_hero_initialize(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
