#ifndef GAW_MD_SERVICE_CLOCK_H
#define GAW_MD_SERVICE_CLOCK_H
#include "source_md_psg_replay.h"

/* Hardware Z80 owns this bytewise publication in68000 RAM. This is a
 * separate protocol,not SourcePsgQueue shared between processors. */
typedef struct {volatile u8 sequence,v,counter_hi,counter_lo,ready,error;} MdServiceStamp;
typedef struct {
    MdServiceStamp *stamp;
    u32 base,reads,retries;
    u16 counter,lines,error;
} MdServiceClock;
enum {MD_SERVICE_OK,MD_SERVICE_INVALID,MD_SERVICE_WAIT,MD_SERVICE_FAULT};
/* Timer starts at the next unambiguous physical V100. epoch is the logical
 * master time at the beginning of that line. One client owner,no reentry.
 * Read at least once per65535physical lines (~4seconds); startup too.
 * Publication period/reader latency must keep sample age below5lines.
 * No BUSREQ after startup,no DMA or other stall reaching that bound.
 * Sequence snapshot must finish within128publications to prevent ABA. */
u8 md_service_clock_init(MdServiceClock *clock,MdServiceStamp *stamp,u16 lines,u32 epoch);
/* Output/time state unchanged on WAIT. Returns a fresh atomic HV time,not
 * the time when the C function returns. Fault is sticky until reinit/reset.
 * No Z80 bus request in this function; all reads are native68000 RAM/HV. */
u8 md_service_clock_now(MdServiceClock *clock,SourceMdPsgReplayClock *output);
/* SDK startup owns/replaces the hardware Z80 driver. Config atZRAM0100.
 * The service only publishes time; gameplay/audio/PSG remain68000 code.
 * Driver image assembled from md_service_clock_z80.asm,256..7936bytes. */
u8 md_service_clock_start(MdServiceStamp *stamp,u16 lines,const u8 *image,u16 bytes);
u16 md_service_clock_hv(void);
#endif
