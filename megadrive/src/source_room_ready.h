#ifndef GAW_SOURCE_ROOM_READY_H
#define GAW_SOURCE_ROOM_READY_H
#include "source_room_load.h"
#include "source_hero_initialize.h"
/* Original24E7 through5B20/1CAF to prefetched1FA7. Source full_ram and compact
 * overlays must already be live. Includes class0/1/2 music dispatch. */
u8 source_room_tail(SourceClock *clock,SourceIrqContext *context,const u8 *rom,
 SourceGraphicsCheckpoint checkpoint,void *user);
/* One16D0 clock through hero/scripts/music to1FA7. All foreground RAM views
 * must alias context->full_ram at their source offsets. No intermediate
 * memory/clock injection. Inherits six-destination class0 map scope;1FA7
 * reveal/fade, physical rendering and global boot entry remain external. */
u8 source_room_load_class0_ready(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *rom,
 SourceActorListData *actors,SourceActorGraphicsData *graphics,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
