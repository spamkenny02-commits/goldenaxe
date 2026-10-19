#include <genesis.h>
#include "md_z80_psg.h"

u8 md_z80_psg_start(MdZ80PsgMailbox *mailbox,u16 lines,const u8 *image,u16 bytes)
{
    u32 physical=(u32)mailbox&0xffffffUL;u16 n;u8 *raw=(u8 *)mailbox;
    if(!mailbox || physical<0xff0000UL || (physical&0x7fff)>32768-sizeof(*mailbox) ||
       !image || bytes<0x200 || bytes>0x1000 || (lines!=262 && lines!=313)) return MD_Z80_PSG_INVALID;
    for(n=0;n<sizeof(*mailbox);n++) raw[n]=0;
    return md_service_clock_start(&mailbox->stamp,lines,image,bytes);
}

u8 md_z80_psg_transfer(MdZ80PsgMailbox *mailbox,const u8 *payload,u8 index,u8 head)
{
    const u8 *source=payload;volatile u8 *destination=(volatile u8 *)(0xa01000UL+(u16)index*22);
    if(!mailbox || !payload || index>=32) return MD_Z80_PSG_INVALID;
    if(!mailbox->grant) return MD_Z80_PSG_WAIT;
    Z80_requestBus(TRUE);
    if(!mailbox->grant) {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    __asm__ volatile (".rept 22\n\tmove.b (%0)+,(%1)+\n\t.endr":"+a"(source),"+a"(destination)::"memory","cc");
    *(volatile u8 *)0xa00106=head;mailbox->head=head;mailbox->grant=0;
    Z80_releaseBus();return MD_Z80_PSG_OK;
}

u8 md_z80_psg_stop(MdZ80PsgMailbox *mailbox)
{
    if(!mailbox) return MD_Z80_PSG_INVALID;
    if(!mailbox->stamp.ready) return MD_Z80_PSG_OK;
    if(mailbox->head!=mailbox->tail || mailbox->busy || !mailbox->grant) return MD_Z80_PSG_WAIT;
    Z80_requestBus(TRUE);
    if(!mailbox->grant) {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    *(volatile u8 *)0xa00107=1;
    Z80_releaseBus();return MD_Z80_PSG_OK;
}
