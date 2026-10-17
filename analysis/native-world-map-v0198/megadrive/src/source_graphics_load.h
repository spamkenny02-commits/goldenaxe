#ifndef GAW_SOURCE_GRAPHICS_LOAD_H
#define GAW_SOURCE_GRAPHICS_LOAD_H
#include "source_pattern_clock.h"

typedef struct {
    u8 *patterns;       /* 16384-byte SMS pattern mirror. */
    u8 *metatiles;      /* 2048 bytes, C900..D0FF. */
    u8 *backup;         /* 16 bytes, C080..C08F. */
    u8 *terrain;        /* 1024 bytes, D100..D4FF. */
    u8 *saved_terrain;  /* 1024 bytes, SRAM9000..93FF. */
} SourceGraphicsData;
typedef u8 (*SourceGraphicsCheckpoint)(void *user,u16 pc,const SourceClock *clock,
                                       const SourceIrqContext *context);

/* Changed class0, display disabled, C0AC=0, as in audited16D0..24B9 path.
 * Source bank2 and11 are each16KiB. patterns starts at bank15:8010 and
 * includes the following metatile stream. Physical mapper/VDP not emulated.
 * Every checkpoint retains the same logical clock/R/IRQ/audio state. */
u8 source_graphics_load_class0(SourceClock *clock,SourceIrqContext *context,
                               const u8 *patterns,const u8 *bank2,const u8 *bank11,
                               SourceGraphicsData *data,SourceGraphicsCheckpoint checkpoint,void *user);
#endif
