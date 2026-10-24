#ifndef GAW_SOURCE_ACTOR_LIST_H
#define GAW_SOURCE_ACTOR_LIST_H
#include "source_graphics_load.h"
typedef struct {
 u8 *actors;             /* C600..C8FF,768 bytes */
 u8 *active_count;       /* C0A2 */
 const u8 *room;         /* C0B9..C0BA */
 const u8 *masks;        /* C200..C2FF */
 const u8 *progression;  /* C0CE..C1CD, indexed by live C037 */
} SourceActorListData;
/* Original1780..1853, excluding1853. Room must be0..511; bank12 is16KiB.
 * Includes original stats, persistence, defeated-boss replacement and count.
 * Shares the caller clock and dynamic IRQ/audio context. Mapper switching
 * is represented by explicit bank data, not a physical mapper write.
 * On failure retain completed writes and stop; no retry/rollback. */
u8 source_actor_list(SourceClock *clock,SourceIrqContext *context,
 const u8 *bank12,SourceActorListData *data,
 SourceGraphicsCheckpoint checkpoint,void *user);
#endif
