#ifndef GAW_SOURCE_CLOCK_H
#define GAW_SOURCE_CLOCK_H
#include <types.h>

typedef struct
{
    u32 period,raster,until_vint,elapsed;
    u32 foreground_tstates,foreground_m1,irq_tstates,irq_m1,irq_count;
    u32 status_suppressions,vector_coalescences;
    u8 refresh,iff,blocked,pending,first;
} SourceClock;

typedef struct { u32 entry_raster,entry_elapsed;u8 entry_refresh; } SourceClockIrq;
typedef struct { u32 tstates,fetches; } SourceClockWork;
typedef u8 (*SourceClockInterrupt)(void *context,const SourceClockIrq *entry,SourceClockWork *work);
enum { SOURCE_CLOCK_NONE,SOURCE_CLOCK_DI,SOURCE_CLOCK_EI,SOURCE_CLOCK_STATUS };

/* Mode4/192,VINT enabled,HINT disabled. Input is after the IRQ check and
 * first opcode fetch. Interrupt work includes accept/vector/body/RET;
 * its callback must model current RAM/audio, never an average frame budget.
 * GPG's local IM1 convention (no extra acknowledge R increment) is retained. */
u8 source_clock_init(SourceClock *clock,u16 lines,u32 raster,u8 refresh,u8 iff,u8 blocked,u8 pending);
u8 source_clock_execute(SourceClock *clock,u16 tstates,u8 fetches,u8 effect,SourceClockInterrupt interrupt,void *context);
u8 source_clock_checkpoint(SourceClock *clock,SourceClockInterrupt interrupt,void *context);
/* Batch stable foreground blocks only while no interrupt can intervene.
 * Blocks have no DI/EI/status effects or RAM writes. Stops at/before VINT;
 * returning zero means use ordinary execution, with no state changed. */
u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions);

#endif
