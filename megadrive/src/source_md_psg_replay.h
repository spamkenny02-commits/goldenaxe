#ifndef GAW_SOURCE_MD_PSG_REPLAY_H
#define GAW_SOURCE_MD_PSG_REPLAY_H
#include "source_psg_queue.h"

typedef struct {
    u32 master;
    u16 vertical,horizontal,lines,error;
} SourceMdPsgReplayClock;
/* H32,Mode5/224/noninterlace,HV latch disabled. line_epoch is the logical
 * master time at the beginning of the sampled physical line,established by
 * the caller. The function does not discover an epoch from ambiguous V. */
u8 source_md_psg_replay_seed(SourceMdPsgReplayClock *clock,u16 lines,u16 hv,u32 line_epoch);
/* Native68000 synchronous consumer of an already prepared contiguous event
 * array (SourcePsgEvent sizeof6). Caller masks IRQs,prohibits DMA and keeps
 * code/data stable. Events are ordered and all due/now spans<2^31. Clock
 * reads must stay less than three physical lines apart,including the interval
 * from the seed sample to entry; missed periods can alias undetectably.
 * Exact630tick pairs/315tick quads are emitted as short fixed bursts.
 * Returns0success,1clockfault; already emitted bytes cannot be rolled back.
 * Clock fields describe the last HV sample,which precedes the final write.
 * This blocks the producer; it is a diagnostic integration path,not an IRQ
 * scheduler or global game epoch. No exact deadline guarantee. Back-to-back
 * quads still incur clock/dispatch overhead between groups; long315tick runs
 * are not accurately paced by this prototype. */
u16 source_md_psg_replay(SourceMdPsgReplayClock *clock,const SourcePsgEvent *events,u16 count);
#endif
