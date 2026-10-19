#include <genesis.h>
#include "md_z80_video_dma.h"

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
