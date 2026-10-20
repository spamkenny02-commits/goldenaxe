#include <genesis.h>
#include "md_z80_video_dma.h"

static u8 job_in_ram(const MdZ80VideoDmaJob *job)
{
    u32 address=(u32)job&0xffffff;
    return job && !(address&1) && address>=0xff0000 && address<=0x1000000-sizeof(*job);
}

u8 md_z80_video_dma_prepare(MdZ80VideoDmaJob *job,const u32 *source,u16 tile)
{
    u32 address=(u32)source,physical=address&0xffffff,token=(u32)job&0xffffff;
    if(!job_in_ram(job) || !source || (address&1) || (address&0x1ffff)>0x1ffe0 || tile>=2048 ||
       VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224 ||
       (physical<token+sizeof(*job) && token<physical+32)) return MD_Z80_PSG_INVALID;
    address>>=1;
    job->source_low=0x9500|(address&255);job->source_mid=0x9600|((address>>8)&255);
    job->source_high=0x9700|((address>>16)&127);
    job->command=VDP_DMA_VRAM_ADDR((u32)tile*32);job->ready=0xd532;
    return MD_Z80_PSG_OK;
}

u8 md_z80_video_dma_try_prepared(MdZ80PsgMailbox *mailbox,MdZ80VideoDmaJob *job)
{
    u8 v,current;u16 low,mid,high;
    volatile u16 *parts,*control=(volatile u16*)VDP_CTRL_PORT;
    if(!mailbox || !job_in_ram(job) || job->ready!=0xd532) return MD_Z80_PSG_INVALID;
    if(mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    if(!mailbox->stamp.ready || !mailbox->grant) return MD_Z80_PSG_WAIT;
    /* The held-bus snapshot below is authoritative. A pre-bus seqlock
     * equality check needlessly rejects candidates while the writer runs.
     * Gate speculative requests on the real beam and current grant only. */
    current=*(volatile u16*)0xc00008>>8;
    if(current<235 || current>252) return MD_Z80_PSG_WAIT;
    /* Only eligible candidates pay for VDP configuration/field loads. */
    VDP_setAutoInc(2);low=job->source_low;mid=job->source_mid;high=job->source_high;
    parts=(volatile u16*)&job->command;
    Z80_requestBus(TRUE);
    if(mailbox->stamp.error) {Z80_releaseBus();return MD_Z80_PSG_FAULT;}
    /* Only the single atomic V byte is used, never the multi-byte counter.
     * An odd counter publication cannot tear V. Stopping that publication
     * is safe when the held-bus grant and independently read V age pass. */
    v=mailbox->stamp.v;
    current=*(volatile u16*)0xc00008>>8;
    if(!mailbox->stamp.ready || !mailbox->grant ||
       v<235 || v>252 || current>252 || (u8)(current-v)>2)
    {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    *control=0x9310;*control=0x9400;
    *control=low;*control=mid;*control=high;
    *control=parts[0];*control=parts[1];
    Z80_releaseBus();job->ready=0;
    return MD_Z80_PSG_OK;
}

u8 md_z80_video_dma_try(MdZ80PsgMailbox *mailbox,const u32 *source,u16 tile)
{
    u8 sequence,v,current;
    u32 address;u16 source_low,source_mid,source_high;
    volatile u32 command;volatile u16 *parts,*control=(volatile u16*)VDP_CTRL_PORT;
    if(!mailbox || !source || ((u32)source&1) || ((u32)source&0x1ffff)>0x1ffe0 || tile>=2048 ||
       VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224) return MD_Z80_PSG_INVALID;
    if(mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    /* Prepare before taking the bus; retain the SDK's memory-word DMA
     * command convention. Auto-increment is SDK-owned even on WAIT. */
    VDP_setAutoInc(2);
    address=(u32)source>>1;
    source_low=0x9500|(address&255);source_mid=0x9600|((address>>8)&255);
    source_high=0x9700|((address>>16)&127);
    command=VDP_DMA_VRAM_ADDR((u32)tile*32);parts=(volatile u16*)&command;
    if(!mailbox->stamp.ready || !mailbox->grant) return MD_Z80_PSG_WAIT;
    sequence=mailbox->stamp.sequence;
    if(sequence&1) return MD_Z80_PSG_WAIT;
    v=mailbox->stamp.v;
    /* Conservative common subset: the raw counter wraps differently in PAL.
     * Rejecting some blank lines is intentional; keep room before frame end. */
    if(v<235 || v>252) return MD_Z80_PSG_WAIT;
    current=*(volatile u16*)0xc00008>>8;
    if(current>252 || (u8)(current-v)>2 || mailbox->stamp.sequence!=sequence) return MD_Z80_PSG_WAIT;
    Z80_requestBus(TRUE);
    if(mailbox->stamp.error) {Z80_releaseBus();return MD_Z80_PSG_FAULT;}
    /* The consumer may have completed a newer publication before BUSACK.
     * It is now stopped: accept that newer complete snapshot, not an odd
     * in-progress publication. Revalidate its V age under the held bus. */
    sequence=mailbox->stamp.sequence;v=mailbox->stamp.v;
    current=*(volatile u16*)0xc00008>>8;
    if(!mailbox->stamp.ready || !mailbox->grant || (sequence&1) ||
       v<235 || v>252 || current>252 || (u8)(current-v)>2)
    {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    /* A fixed32byte transfer: no generic dispatch or address arithmetic in
     * the critical section. DMA command words are read from RAM, as in SGDK. */
    *control=0x9310;*control=0x9400;
    *control=source_low;*control=source_mid;*control=source_high;
    *control=parts[0];*control=parts[1];
    Z80_releaseBus();
    return MD_Z80_PSG_OK;
}
