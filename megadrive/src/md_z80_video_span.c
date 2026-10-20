#include <genesis.h>
#include "md_z80_video_span.h"

static u8 in_ram(const MdZ80VideoSpan *job)
{
    u32 address=(u32)job&0xffffff;
    return job && !(address&1) && address>=0xff0000 && address<=0x1000000-sizeof(*job);
}

u8 md_z80_video_span_prepare(MdZ80VideoSpan *job,const u32 *source,u16 tile,u16 count)
{
    u32 address=(u32)source,physical=address&0xffffff,token=(u32)job&0xffffff;
    u16 bytes;
    if(!in_ram(job) || !source || (address&1) || !count || count>4 || tile>2048-count ||
       VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224) return MD_Z80_PSG_INVALID;
    bytes=count*32;
    if((address&0x1ffff)>0x20000UL-bytes ||
       (physical<token+sizeof(*job) && token<physical+bytes)) return MD_Z80_PSG_INVALID;
    address>>=1;
    job->source_low=0x9500|(address&255);job->source_mid=0x9600|((address>>8)&255);
    job->source_high=0x9700|((address>>16)&127);job->length_low=0x9300+count*16;
    job->command=VDP_DMA_VRAM_ADDR((u32)tile*32);job->ready=0xd580;
    return MD_Z80_PSG_OK;
}

u8 md_z80_video_span_try(MdZ80PsgMailbox *mailbox,MdZ80VideoSpan *job)
{
    u8 v,current,age;u16 low,mid,high,length;
    volatile u16 *parts,*control=(volatile u16*)VDP_CTRL_PORT;
    if(!mailbox || !in_ram(job) || job->ready!=0xd580) return MD_Z80_PSG_INVALID;
    if(mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    if(!mailbox->stamp.ready || !mailbox->grant) return MD_Z80_PSG_WAIT;
    current=*(volatile u16*)0xc00008>>8;
    if(current<235 || current>252) return MD_Z80_PSG_WAIT;
    VDP_setAutoInc(2);low=job->source_low;mid=job->source_mid;high=job->source_high;
    length=job->length_low;age=length==0x9310?2:1;parts=(volatile u16*)&job->command;
    Z80_requestBus(TRUE);
    if(mailbox->stamp.error) {Z80_releaseBus();return MD_Z80_PSG_FAULT;}
    v=mailbox->stamp.v;current=*(volatile u16*)0xc00008>>8;
    if(!mailbox->stamp.ready || !mailbox->grant || v<235 || v>252 ||
       current>252 || (u8)(current-v)>age)
    {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    *control=length;*control=0x9400;*control=low;*control=mid;*control=high;
    *control=parts[0];*control=parts[1];
    Z80_releaseBus();job->ready=0;
    return MD_Z80_PSG_OK;
}

static inline __attribute__((always_inline)) u8 in_window_mask(u8 v,u32 allowed)
{
    if(v<224) return 0;
#ifdef SGDK_GCC
    /* Register BTST masks its bit index modulo32: rawV224 selects bit0.
     * Bits5..10 exclude the six duplicated NTSC counter values. */
    u8 valid;
    __asm__("btst %2,%1\n\tsne %0" : "=d"(valid) : "d"(allowed),"d"(v) : "cc");
    return valid;
#else
    return (allowed&(1UL<<(v&31)))!=0;
#endif
}


static inline __attribute__((always_inline)) u8 in_window(u8 v)
{
    return in_window_mask(v,0x1ffff81fUL);
}

u8 md_z80_video_span_try_refresh(MdZ80PsgMailbox *mailbox,MdZ80VideoSpan *job)
{
    u8 v,current,age,grant,ready,large;u16 low,mid,high,length;u32 window;
    volatile u16 *parts,*control=(volatile u16*)VDP_CTRL_PORT;
    if(!mailbox || !in_ram(job) || (job->ready!=0xd580 && job->ready!=0xd600)) return MD_Z80_PSG_INVALID;
    if(mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    ready=mailbox->stamp.ready;
    if(!ready) return MD_Z80_PSG_WAIT;
    if(!(ready&MD_Z80_VIDEO_SPAN_REFRESH_CAP)) return MD_Z80_PSG_INVALID;
    length=job->length_low;large=length>0x9340;
    if(large) {
        if(!(ready&MD_Z80_VIDEO_SPAN_GRANT_CAP)) return MD_Z80_PSG_INVALID;
        if(mailbox->busy || mailbox->head!=mailbox->tail) return MD_Z80_PSG_WAIT;
    }
    if(!mailbox->grant) return MD_Z80_PSG_WAIT;
    window=(large || (ready&MD_Z80_VIDEO_SPAN_GRANT_CAP))?0x0ffff81fUL:0x1ffff81fUL;
    current=*(volatile u16*)0xc00008>>8;
    if(!in_window_mask(current,window)) return MD_Z80_PSG_WAIT;
    VDP_setAutoInc(2);low=job->source_low;mid=job->source_mid;high=job->source_high;
    age=large?0:(length==0x9310?2:1);parts=(volatile u16*)&job->command;
    Z80_requestBus(TRUE);
    if(mailbox->stamp.error) {Z80_releaseBus();return MD_Z80_PSG_FAULT;}
    grant=mailbox->grant;v=large?(0x80|(grant>>1)):mailbox->stamp.v;current=*(volatile u16*)0xc00008>>8;
    if(!mailbox->stamp.ready || !grant ||
       (large && (mailbox->busy || mailbox->head!=mailbox->tail)) || !in_window_mask(v,window) ||
       !in_window_mask(current,window) || (u8)(current-v)>age)
    {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    *control=length;*control=0x9400;*control=low;*control=mid;*control=high;
    *control=parts[0];*control=parts[1];
    Z80_releaseBus();job->ready=0;
    return MD_Z80_PSG_OK;
}

u8 md_z80_video_span_prepare_refresh(MdZ80VideoSpan *job,const u32 *source,u16 tile,u16 count)
{
    u32 address=(u32)source,physical=address&0xffffff,token=(u32)job&0xffffff;
    u16 bytes;
    if(!in_ram(job) || !source || (address&1) || !count || count>8 || tile>2048-count ||
       VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224) return MD_Z80_PSG_INVALID;
    bytes=count*32;
    if((address&0x1ffff)>0x20000UL-bytes ||
       (physical<token+sizeof(*job) && token<physical+bytes)) return MD_Z80_PSG_INVALID;
    address>>=1;
    job->source_low=0x9500|(address&255);job->source_mid=0x9600|((address>>8)&255);
    job->source_high=0x9700|((address>>16)&127);job->length_low=0x9300+count*16;
    job->command=VDP_DMA_VRAM_ADDR((u32)tile*32);job->ready=0xd600;
    return MD_Z80_PSG_OK;
}

/* Hidden H32 path: same small retained tokens, whole-frame DMA bandwidth.
 * Raw229..234 excluded to avoid the duplicated NTSC counter interval. */
u8 md_z80_video_span_try_hidden(MdZ80PsgMailbox *mailbox,MdZ80VideoSpan *job)
{
    u8 v,current,age;u16 low,mid,high,length;
    volatile u16 *parts,*control=(volatile u16*)VDP_CTRL_PORT;
    if(!mailbox || !in_ram(job) || (job->ready!=0xd580 && job->ready!=0xd600) ||
       job->length_low>0x9340 || VDP_isEnable() || VDP_getScreenWidth()!=256 ||
       VDP_getScreenHeight()!=224) return MD_Z80_PSG_INVALID;
    if(mailbox->stamp.error) return MD_Z80_PSG_FAULT;
    if(!mailbox->stamp.ready) return MD_Z80_PSG_WAIT;
    if(!(mailbox->stamp.ready&MD_Z80_VIDEO_SPAN_REFRESH_CAP)) return MD_Z80_PSG_INVALID;
    if(!mailbox->grant) return MD_Z80_PSG_WAIT;
    VDP_setAutoInc(2);low=job->source_low;mid=job->source_mid;high=job->source_high;
    length=job->length_low;age=length==0x9310?2:1;parts=(volatile u16*)&job->command;
    Z80_requestBus(TRUE);
    if(mailbox->stamp.error) {Z80_releaseBus();return MD_Z80_PSG_FAULT;}
    v=mailbox->stamp.v;current=*(volatile u16*)0xc00008>>8;
    if(!mailbox->stamp.ready || !mailbox->grant || VDP_isEnable() ||
       (v>=229 && v<=234) || (current>=229 && current<=234) || (u8)(current-v)>age)
    {Z80_releaseBus();return MD_Z80_PSG_WAIT;}
    *control=length;*control=0x9400;*control=low;*control=mid;*control=high;
    *control=parts[0];*control=parts[1];
    Z80_releaseBus();job->ready=0;return MD_Z80_PSG_OK;
}
