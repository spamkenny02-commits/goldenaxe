#ifndef GAW_SOURCE_PATTERN_CLOCK_H
#define GAW_SOURCE_PATTERN_CLOCK_H
#include "source_irq_context.h"

/* Prefix sums at complete ROM-command boundaries, generated from032A.
 * A plan must describe the exact immutable ROM stream passed to the loader. */
typedef struct {u32 ticks,fetches;u16 source,decoded;} SourcePatternBoundary;
typedef struct {
    const SourcePatternBoundary *boundary;
    const u8 *decoded;
    u16 count;
} SourcePatternPlane;
typedef struct {SourcePatternPlane planes[4];} SourcePatternPlan;

/* Audited changed class0 loading path 16D0..1706. Graphics output goes to a
 * caller-owned SMS pattern mirror. Entry phase/R and RAM/audio must be real
 * logical state; no resource-average delay or captured phase lookup is used.
 * Scope: ordinary class0 bank change, display disabled, full IRQ gate clear.
 * This component does not perform physical Mega Drive VRAM uploads. */
u8 source_graphics_prefix_class0(SourceClock *clock,SourceIrqContext *context,
                                 const u8 *patterns,u8 *destination,const u8 **end);
u8 source_graphics_prefix_class0_planned(SourceClock *clock,SourceIrqContext *context,
                                 const u8 *patterns,u8 *destination,const u8 **end,
                                 const SourcePatternPlan *plan);
#endif
