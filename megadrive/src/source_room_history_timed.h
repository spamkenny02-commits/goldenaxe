#ifndef GAW_SOURCE_ROOM_HISTORY_TIMED_H
#define GAW_SOURCE_ROOM_HISTORY_TIMED_H
#include "source_rng_timed.h"
typedef struct {u8 *room,*seed,*history,*masks;} SourceRoomHistoryData;
typedef struct {u8 calls,restored,last_value;} SourceRoomHistoryOutput;
/* Original1C15..1C90, including RET. All pointers are live source bytes:
 * room/seed little-endian2, DCF0 history16, C200 masks256. Entry follows
 * SourceClock prefetch convention. IRQ-visible writes commit per opcode;
 * failure retains completed effects and caller must stop, not retry.
 * Does not invent an entry clock or integrate a native frame counter. */
u8 source_room_history_timed(SourceClock *clock,SourceRoomHistoryData *data,
 SourceRoomHistoryOutput *output,SourceClockInterrupt interrupt,void *context);
/* Original24BF ->1780: clear C090..C0AF and C4B0..C5FF, then history.
 * Byte copies remain visible at each repeated LDIR boundary. Stops at the
 * prefetched enemy-loader entry; does not execute1780 itself. */
u8 source_room_actor_prefix(SourceClock *clock,u8 *flags,u8 *objects,
 SourceRoomHistoryData *data,SourceRoomHistoryOutput *output,
 SourceClockInterrupt interrupt,void *context);
#endif
