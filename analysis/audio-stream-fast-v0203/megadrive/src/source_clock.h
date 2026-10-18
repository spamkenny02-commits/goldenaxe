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
 * Entry/exit interrupt mask and EI-delay must match; no status reads or
 * VDP interrupt configuration changes. Paired DI/EI inside a block is safe
 * only when its delay has expired at block end. Commit the block's data
 * writes before the next clock operation. Stops at/before VINT; returning
 * zero means use ordinary execution, with no state changed. */
u16 source_clock_repeat(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions);
/* One stable block, under the same contract as repeat. Inlining avoids
 * general repetition arithmetic and register spills at constant call sites.
 * Requires a clock initialized by source_clock_init (until_vint<=period). */
static inline u8 source_clock_block(SourceClock *clock,u16 tstates,u16 fetches)
{
    u32 master=(u32)tstates*15;
    if(!tstates || !fetches || clock->first || clock->blocked ||
       clock->pending || !clock->iff || master>clock->until_vint) return 0;
    clock->elapsed+=master;
    clock->raster+=master;
    if(clock->raster>=clock->period) clock->raster-=clock->period;
    clock->until_vint-=master;
    if(!clock->until_vint) {clock->until_vint=clock->period;clock->pending=1;}
    clock->foreground_tstates+=tstates;clock->foreground_m1+=fetches;
    clock->refresh=(clock->refresh&128)|((clock->refresh+fetches)&127);
    return 1;
}
/* Ordinary instructions retain the full boundary handler whenever a block
 * cannot run, including prefetched opcodes, EI delay and pending IRQs. */
static inline u8 source_clock_plain(SourceClock *clock,u16 tstates,u8 fetches,
                                   SourceClockInterrupt interrupt,void *context)
{
    return source_clock_block(clock,tstates,fetches) ||
           source_clock_execute(clock,tstates,fetches,SOURCE_CLOCK_NONE,interrupt,context);
}
/* Stable blocks with IRQs disabled; may cross VINT(s), preserving pending.
 * No DI/EI/status or observable RAM effects inside the block. Returns zero
 * without mutation for prefetched/blocked/enabled/overflowing inputs. */
u16 source_clock_repeat_disabled(SourceClock *clock,u16 tstates,u8 fetches,u16 repetitions);

#endif
