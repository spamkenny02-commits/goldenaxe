#ifndef GAW_SOURCE_ROOM_FINISH_H
#define GAW_SOURCE_ROOM_FINISH_H
#include "source_room_hud.h"
typedef struct {u16 wait_taken;u8 error;} SourceRoomFinish;
/* Foreground palette preparation1DEB..24BF, excluding its caller. */
u8 source_room_palette(SourceClock *clock,SourceIrqContext *context,SourceWorldMapData *map,
                        const u8 *hud,SourceGraphicsCheckpoint checkpoint,void *user);
/* From1DE8 via229C/0B95 to24BF. Shares clock/RAM/audio with preceding
 * graphics/map/HUD. The logical name table is copied to patterns+3800;
 * palette slots occupy cells+B0 (DCB0..DCBF), as in the source memory.
 * Physical VDP/SAT/CRAM and real-time pacing remain the renderer's job. */
u8 source_room_finish(SourceClock *clock,SourceIrqContext *context,
                       SourceGraphicsData *graphics,SourceWorldMapData *map,const u8 *hud,
                       SourceRoomFinish *result,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
