#include <genesis.h>
#include "md_service_clock.h"

u8 md_service_clock_start(MdServiceStamp *stamp,u16 lines,const u8 *image,u16 bytes)
{
    u32 physical=(u32)stamp&0xffffffUL;u16 bank,address;
    if(!stamp || !image || bytes<0x106 || bytes>0x1f00 || (lines!=262 && lines!=313) ||
       physical<0xff0000UL || (physical&0x7fff)>0x7ffa) return MD_SERVICE_INVALID;
    stamp->sequence=stamp->v=stamp->counter_hi=stamp->counter_lo=stamp->ready=stamp->error=0;
    address=0x8000|(physical&0x7fff);bank=physical>>15;
    Z80_loadCustomDriver(image,bytes);
    Z80_requestBus(TRUE);
    Z80_write(0x100,address);Z80_write(0x101,address>>8);
    Z80_write(0x102,bank);Z80_write(0x103,bank>>8);
    Z80_write(0x104,lines-256);Z80_write(0x105,1);
    Z80_releaseBus();return MD_SERVICE_OK;
}
