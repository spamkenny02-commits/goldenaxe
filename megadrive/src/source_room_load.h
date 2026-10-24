#ifndef GAW_SOURCE_ROOM_LOAD_H
#define GAW_SOURCE_ROOM_LOAD_H
#include "source_room_finish.h"
#include "source_room_history_timed.h"
#include "source_actor_list.h"
#include "source_actor_graphics.h"

typedef struct {
 const u8 *patterns,*bank2,*bank11,*map_bank,*bank4,*hud;
 u8 map_flags;
} SourceRoomLoadInput;
typedef struct {
 SourceGraphicsData *graphics;
 SourceWorldMapData *map;
 u8 *room;       /* live C0B9..C0BA, little endian */
 u8 *flags;      /* C090..C0AF,32 bytes */
 u8 *objects;    /* C4B0..C5FF,336 bytes */
 u8 *masks;      /* C200..C2FF,256 bytes */
} SourceRoomLoadData;
typedef struct {
 SourceRoomFinish finish;
 SourceRoomHistoryOutput history;
 u8 completed;
} SourceRoomLoadOutput;

/* One continuous logical16D0 ->1780 clock, including dynamic native IRQ/audio.
 * Scope inherits changed-class0 graphics and the six audited saved-bit0
 * outdoor map destinations. Seed aliases context->ram+28, history aliases
 * map->cells+F0. Caller supplies those live bytes before entering; no later
 * clock/R/seed/history injection occurs. Stops at prefetched1780, before
 * enemy loading. Physical rendering/pacing and the boot entry clock are
 * external. Failure retains completed effects: stop, never retry in place. */
u8 source_room_load_class0(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user);
/* Extend the same chain to prefetched1853, including actor list/stats/count.
 * Actor room/mask/count views must alias the loading views. Graphics for
 * those actors, beginning at1853, remain the following stage. */
u8 source_room_load_class0_actors(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *bank12,
 SourceActorListData *actors,SourceRoomLoadOutput *output,
 SourceGraphicsCheckpoint checkpoint,void *user);
/* Extend to prefetched18E1 after actor allocation/RLE/remapping. ROM is the
 * original immutable256KiB image. Actor and graphics views must alias those
 * of the preceding loading stages. Does not include the18E1 RET or hero/tail. */
u8 source_room_load_class0_graphics(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *rom,
 SourceActorListData *actors,SourceActorGraphicsData *graphics,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
