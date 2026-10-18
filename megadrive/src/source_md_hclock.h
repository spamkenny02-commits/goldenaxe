#ifndef GAW_SOURCE_MD_HCLOCK_H
#define GAW_SOURCE_MD_HCLOCK_H
#include <types.h>

/* Standard H32, Mode5,224-line,non-interlaced HV samples only. The VDP HV
 * latch must be disabled. Caller supplies an established frame origin and
 * physical line for the seed; this module does not discover a boot epoch.
 * master/phase are lower bounds,quantized to20 master ticks. */
typedef struct {u32 master,phase;u16 lines;} SourceMdHClock;
enum {SOURCE_MD_HCLOCK_OK,SOURCE_MD_HCLOCK_INVALID,SOURCE_MD_HCLOCK_GAP};
u8 source_md_hclock_seed(SourceMdHClock *clock,u8 pal,u16 line,u16 hv,u32 origin);
/* Sample often enough: actual elapsed time must be <20500 master ticks on
 * NTSC,<194920 on PAL. Longer gaps can alias and cannot always be detected.
 * Invalid/implausible samples leave state unchanged. One owner,no reentry.
 * Interrupt/display/DMA latency counts towards that sampling obligation. */
u8 source_md_hclock_sample(SourceMdHClock *clock,u16 hv);
#endif
