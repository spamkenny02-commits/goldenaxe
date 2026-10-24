#ifndef GAW_SOURCE_ROOM_CONTOURS_H
#define GAW_SOURCE_ROOM_CONTOURS_H
#include "source_room_reveal.h"
#include "source_vdp_dirty.h"
/* Original1FB6 through prefetched2002 (before RET). Reads the live D600 map,
 * writes its16 contours into16KiB VRAM, with both source waits per contour.
 * Callback points0B95/0BB3 expose each wait; final2002 is before RET.
 * VRAM may already have been partly published on failure. */
u8 source_room_contours(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,u8 *vram,SourceGraphicsCheckpoint checkpoint,void *user);
/* Same execution, accumulating foreground writes for incremental delivery.
 * Bind the IRQ video producer to the same dirty object; consumer owns clear. */
u8 source_room_contours_marked(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,u8 *vram,SourceVdpDirty *dirty,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
