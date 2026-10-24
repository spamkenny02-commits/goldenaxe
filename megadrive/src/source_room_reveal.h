#ifndef GAW_SOURCE_ROOM_REVEAL_H
#define GAW_SOURCE_ROOM_REVEAL_H
#include "source_room_ready.h"
#include "source_wait_restore.h"

/* Original1FA7..0ACE, before the palette fade. One continuous source clock;
 * full_ram and compact overlays stay live. Optional16KiB VRAM receives only
 * the foreground3800..3DFF clear: IRQ video publication remains external.
 * ROM is the original256KiB cartridge. Does not install physical MD video. */
u8 source_room_reveal_prepare(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,u8 *vram,SourceGraphicsCheckpoint checkpoint,void *user);
/* Original0ACE..0B09, including the two0B95 waits for every changed palette
 * step, then RET to prefetched1FB6. Palette bytes are live DCA0/DCC0. */
u8 source_room_reveal_fade(SourceClock *clock,SourceIrqContext *context,
 const u8 *rom,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
