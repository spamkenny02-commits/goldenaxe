#ifndef GAW_SOURCE_ROOM_HUD_H
#define GAW_SOURCE_ROOM_HUD_H
#include "source_world_map.h"
/* Original1E4E alone, excluding its CALL instruction. Supports byte-valued
 * gauges including DJNZ0 ->256 and their original DC/DD memory overlap. */
u8 source_hud_prepare(SourceClock *clock,SourceIrqContext *context,
                       SourceWorldMapData *map,const u8 *bank4,const u8 *hud);
/* From24BC through1DE2/2279 and1E4E to1DE8. HUD input bytes:
 * health,max health,magic,max magic,gold,9 gem flags,2 later palette inputs.
 * RAM/clock/audio remain shared. bank4 supplies the original HUD map.
 * This prepares RAM tile words; no physical VDP upload or wait here. */
u8 source_room_hud_prepare(SourceClock *clock,SourceIrqContext *context,
                            SourceGraphicsData *graphics,SourceWorldMapData *map,
                            const u8 *bank4,const u8 *hud,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
