#ifndef GAW_MD_PSG_SERVICE_H
#define GAW_MD_PSG_SERVICE_H
#include "md_service_clock.h"
#include "source_md_psg_plan.h"

/* Single 68000 cooperative consumer. Producer publishes complete FIFO
 * packets; only this service removes events. No producer reentry/IRQ/DMA.
 * Clock epoch is physical line100, all due offsets<32760 physical lines.
 * Stable caller-owned storage lives until reset; errors latch and stop IO.
 * A prepared block owns copied bytes, so its FIFO slots may be reused. */
typedef struct {
    MdServiceClock *clock;
    SourcePsgQueue *queue;
    SourceMdPsgReplayClock physical;
    SourceMdPsgBlock blocks[32];
    u16 gates[32],read,write;
    u32 epoch,emitted,prepared,waits;
    u16 gate,armed,error,lead;
} MdPsgService;

u8 md_psg_service_init(MdPsgService *service,MdServiceClock *clock,SourcePsgQueue *queue,u32 epoch,u16 lead);
/* Prepare ready groups without waiting. Call after each packet publication.
 * Cache full leaves the remaining events in the bounded publication FIFO. */
u8 md_psg_service_prepare(MdPsgService *service);
/* Called only when the cheap gate allows a physical clock check. Can wait
 * up to lead+1 lines before nearby prepared groups; caller bounds tick gaps.
 * Groups within60000 master ticks are replayed together,not re-prepared
 * between closely spaced PSG writes. No exact-deadline guarantee. */
u8 md_psg_service_dispatch(MdPsgService *service);
u8 md_psg_service_flush(MdPsgService *service);
static inline u8 md_psg_service_tick(MdPsgService *service)
{
    MdServiceStamp *stamp;u16 counter;
    if(service->error) return 0;
    if(!service->armed) return 1;
    stamp=service->clock->stamp;
    /* A torn coarse count may trigger early. dispatch checks the full
     * seqlock/HV clock before waiting; this is only a conservative gate. */
    counter=((u16)stamp->counter_hi<<8)|stamp->counter_lo;
    if((s16)(counter-service->gate)<0) return 1;
    return md_psg_service_dispatch(service);
}
#endif
