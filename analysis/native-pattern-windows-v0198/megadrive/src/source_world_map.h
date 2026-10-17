#ifndef GAW_SOURCE_WORLD_MAP_H
#define GAW_SOURCE_WORLD_MAP_H
#include "source_graphics_load.h"
typedef struct {
    u8 *cells;    /* 256 bytes, DC00..DCFF. DD00..DDFF aliases context RAM. */
    u8 *tilemap;  /* 1536 bytes, D600..DBFF; sparse patches before1DE2. */
    u8 metadata[3]; /* C06E..C070. */
} SourceWorldMapData;

/* From24B9 through CALL190B to24BC on the same clock/context.
 * Scope: six audited outdoor destinations, saved bit0 set,C0AC0,C041!=5.
 * map_bank is bank8 or9 according to room; bank2 supplies metadata. */
u8 source_world_map_load(SourceClock *clock,SourceIrqContext *context,u16 room,u8 flags,
                          const u8 *map_bank,const u8 *bank2,SourceGraphicsData *graphics,
                          SourceWorldMapData *map,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
