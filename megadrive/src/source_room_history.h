#ifndef GAW_SOURCE_ROOM_HISTORY_H
#define GAW_SOURCE_ROOM_HISTORY_H
#include <types.h>
typedef u8 (*SourceRoomDraw)(void *context);
/* 1C15: shared DCF0 queue and C200 masks; room high byte selects rules. */
u8 source_room_history(u16 room,u8 *history,u8 *masks,SourceRoomDraw draw,void *context);
#endif
