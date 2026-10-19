#ifndef GAW_MD_Z80_PSG_H
#define GAW_MD_Z80_PSG_H
#include "md_service_clock.h"
#include "source_md_psg_plan.h"

/* Separate protocol,not SourcePsgQueue shared across CPUs. Status is in68k
 * RAM,Z80 writes it but cannot read it. Commands/head/stop live in Z80RAM.
 * Byte cursors wrap modulo256; at most32 published descriptors. */
typedef struct {
    MdServiceStamp stamp;
    volatile u8 head,tail,grant,busy;
} MdZ80PsgMailbox;
typedef struct {
    MdZ80PsgMailbox *mailbox;
    MdServiceClock *clock;
    u32 last_due,published;
    u16 physical_line,counter,error;
} MdZ80PsgProducer;
enum {MD_Z80_PSG_OK,MD_Z80_PSG_INVALID,MD_Z80_PSG_FULL,MD_Z80_PSG_ORDER,MD_Z80_PSG_FAULT,MD_Z80_PSG_WAIT};
/* Cold clock at100,initialized before first read. One clock owner. Call
 * refresh at least once per65535physical lines even during quiet periods.
 * H32/mode5/224,masked native IRQs,no DMA. Bounded BUSREQ transfers are
 * allowed only under a Z80 grant,cleared well before an upcoming burst.
 * Caller publishes early enough for copy/wait;not deadline checked. */
u8 md_z80_psg_init(MdZ80PsgProducer *producer,MdZ80PsgMailbox *mailbox,MdServiceClock *clock);
u8 md_z80_psg_refresh(MdZ80PsgProducer *producer);
/* One complete descriptor or no publication; count0 is a no-op,count>1
 * is invalid. FULL/invalid/order/WAIT keep head,payload,
 * producer counts and last due unchanged. Clock diagnostics may advance on
 * long-horizon refresh. Copies values before one atomic byte head store.
 * All dates within32760lines of clock base,source order spans<2^31. */
u8 md_z80_psg_push(MdZ80PsgProducer *producer,const SourceMdPsgBlock *blocks,u16 count);
/* Synchronous one-descriptor variant. Prepare/validate once, then attempt
 * the same bounded transfer up to attempts times while it returns WAIT.
 * attempts must be nonzero. FULL/other errors return immediately. Single
 * producer/clock owner; block/session must remain intact until return.
 * WAIT exhaustion leaves publication state unchanged, as with push. */
u8 md_z80_psg_push_poll(MdZ80PsgProducer *producer,const SourceMdPsgBlock *block,u16 attempts);
u8 md_z80_psg_start(MdZ80PsgMailbox *mailbox,u16 lines,const u8 *image,u16 bytes);
u8 md_z80_psg_transfer(MdZ80PsgMailbox *mailbox,const u8 *payload,u8 index,u8 head);
u8 md_z80_psg_stop(MdZ80PsgMailbox *mailbox);
#endif
