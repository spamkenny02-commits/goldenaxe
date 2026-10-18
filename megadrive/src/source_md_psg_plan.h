#ifndef GAW_SOURCE_MD_PSG_PLAN_H
#define GAW_SOURCE_MD_PSG_PLAN_H
#include "source_md_psg_replay.h"

/* size28: metadata followed by right-aligned bytes. skip selects a
 * suffix of the fixed315x16/630x8 instruction stream. No host pointers. */
typedef struct {u32 due;u16 skip,count,spacing,target_hv;u8 values[16];} SourceMdPsgBlock;
/* Prepare before seeding the physical clock. Events are ordered within a
 * <2^31 master window,including unsignedwrap. Atomic on error: output/count
 * unchanged. Empty input accepts null arrays. Caller keeps arrays disjoint.
 * Return queue OK/INVALID/FULL/ORDER. Runs longer than16at315 or8at630 split
 * into blocks; interblock overhead still exists for those longer runs. */
u8 source_md_psg_plan(const SourcePsgEvent *events,u16 count,SourceMdPsgBlock *blocks,u16 capacity,u16 *block_count);
/* Optional coarse-clock -> short beam wait targets. epoch is the logical
 * time at the beginning of the caller-established physical seed line.
 * Prepare before seeding. Reject negative/>=2^31 due offsets atomically.
 * Targets round upwards to20tickH32 steps,including line/frame carries. */
u8 source_md_psg_plan_beam(SourceMdPsgBlock *blocks,u16 count,u16 lines,u16 seed_line,u32 epoch);
/* Same critical-section/epoch contract as source_md_psg_replay,except the
 * maximum sampling interval is three physical lines. Caller uses only
 * validated blocks from source_md_psg_plan and preserves them until return.
 * Unlike the raw entry,this entry refreshes the clock after the final IO. */
u16 source_md_psg_replay_planned(SourceMdPsgReplayClock *clock,const SourceMdPsgBlock *blocks,u16 block_count);
#endif
