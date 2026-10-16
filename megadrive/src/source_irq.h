#ifndef GAW_SOURCE_IRQ_H
#define GAW_SOURCE_IRQ_H
#include "source_clock.h"
enum {SOURCE_IRQ_SAT64,SOURCE_IRQ_SAT128,SOURCE_IRQ_TILES,SOURCE_IRQ_HUD,
      SOURCE_IRQ_PALETTE,SOURCE_IRQ_QUEUE,SOURCE_IRQ_MAP_AUDIO,SOURCE_IRQ_AUDIO,
      SOURCE_IRQ_POST_AUDIO,SOURCE_IRQ_STAGES};
typedef struct {
    u32 raster;
    u16 lines,tile_count;
    u8 joy,reset_mask,compensation;
} SourceIrqInput;
typedef struct {
    SourceClockWork stages[SOURCE_IRQ_STAGES],whole;
    u16 palette_taken;
    u8 reset_requested;
} SourceIrqOutput;
/* RAM: C000..C04F then DD00..DDFF. Raster is at0137, after vector/accept.
 * tile_count is decoded from the original pending tile asset (1..256).
 * reader is the native8000 work, without its CALL. Computes IRQ RAM effects
 * and work; SGDK video uploads remain separate. Whole includes72T/6M1 vector
 * plus finalRET, except a requested reset which ends at the009A jump.
 * Failed uncaptured RAM/queue/raster inputs roll back all336 bytes. */
u8 source_irq(u8 *state,const SourceIrqInput *input,const SourceClockWork *reader,
               SourceIrqOutput *output);
#endif
