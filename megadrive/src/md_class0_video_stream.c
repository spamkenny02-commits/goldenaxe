#include "md_class0_video_stream.h"
#include "source_class0_video.h"
#ifndef MD_CLASS0_PALETTE_TRACE
#define MD_CLASS0_PALETTE_TRACE(value) ((void)0)
#endif

u8 md_class0_video_stream_begin(MdClass0VideoStream *s,u8 verify)
{
    if(!s || (s->ready && !s->done) || VDP_getScreenWidth()!=256 ||
       VDP_getScreenHeight()!=224 || VDP_getPlaneWidth()!=64 || VDP_getPlaneHeight()!=32)
        return MD_Z80_PSG_INVALID;
    s->pattern_cursor=s->map_row=s->address=s->count=0;
    s->kind=s->last_kind=s->error=s->done=0;s->job.ready=0;
    s->ready=1;s->verify=verify;s->readback_words=s->readback_errors=0;
    return MD_Z80_PSG_OK;
}
u8 md_class0_video_stream_map(MdClass0VideoStream *s,const u8 *sms)
{
    if(!s || !sms || ((u32)sms&1) || s->ready!=1 || s->error) return MD_Z80_PSG_INVALID;
    source_class0_video_map(sms,s->map,768);s->ready|=2;return MD_Z80_PSG_OK;
}
u8 md_class0_video_stream_palette(MdClass0VideoStream *s,const u8 *upper)
{
    if(!s || !upper || s->ready!=3 || s->error) return MD_Z80_PSG_INVALID;
    source_class0_video_palette(upper,s->palette);s->ready|=4;return MD_Z80_PSG_OK;
}
u8 md_class0_video_stream_step(MdClass0VideoStream *s,MdZ80PsgMailbox *mailbox)
{
    u8 status,v;u16 n,errors,words;const u16 *expected;
    if(!s || !mailbox) return MD_Z80_PSG_INVALID;
    if(s->error || mailbox->stamp.error) {s->error=1;return MD_Z80_PSG_FAULT;}
    if(!mailbox->stamp.ready) return MD_Z80_PSG_WAIT;
    if(!(mailbox->stamp.ready&MD_Z80_VIDEO_SPAN_REFRESH_CAP)) return MD_Z80_PSG_INVALID;
    if(!s->ready || s->done) return MD_Z80_PSG_WAIT;
    if(!s->kind) {
        if(s->pattern_cursor<193) {
            const u32 *rom=source_class0_video_patterns()+(u32)s->pattern_cursor*8;
            s->count=193-s->pattern_cursor;if(s->count>4) s->count=4;
            /* RAM copy avoids a ROM asset straddling a128KiB DMA bank. */
            for(n=0;n<s->count*8;n++) s->payload[n]=rom[n];
            s->address=(16+s->pattern_cursor)*32;s->kind=1;
            status=md_z80_video_span_prepare_refresh(&s->job,s->payload,s->address/32,s->count);
        } else if((s->ready&2) && s->map_row<24) {
            s->count=2;s->address=VDP_getPlaneAddress(BG_A,0,2+s->map_row);s->kind=2;
            status=md_z80_video_span_prepare_refresh(&s->job,(const u32*)(s->map+s->map_row*32),s->address/32,2);
        } else if(s->ready==7 && s->map_row==24) {
            v=*(volatile u16*)0xc00008>>8;
            if(v<235 || v>243) return MD_Z80_PSG_WAIT;
            /* CPU writes do not seize the Z80 bus; bracket for physical audit. */
            MD_CLASS0_PALETTE_TRACE(0x3b);
            PAL_setColors(0,s->palette,32,CPU);
            if(s->verify) {
                *(volatile u32*)VDP_CTRL_PORT=VDP_READ_CRAM_ADDR(0);
                errors=0;
                for(n=0;n<32;n++) if((*(volatile u16*)VDP_DATA_PORT&0x0eee)!=s->palette[n]) errors++;
                s->readback_errors+=errors;s->readback_words+=32;
                if(s->readback_errors) {s->error=1;return MD_Z80_PSG_FAULT;}
            }
            MD_CLASS0_PALETTE_TRACE(0x3c);
            s->done=1;s->last_kind=3;return MD_Z80_PSG_OK;
        } else return MD_Z80_PSG_WAIT;
        if(status) {s->error=1;return status;}
    }
    status=md_z80_video_span_try_refresh(mailbox,&s->job);
    if(status!=MD_Z80_PSG_OK) {if(status==MD_Z80_PSG_FAULT) s->error=1;return status;}
    expected=s->kind==1?(const u16*)s->payload:s->map+s->map_row*32;
    if(s->verify) {
        *(volatile u32*)VDP_CTRL_PORT=VDP_READ_VRAM_ADDR(s->address);
        errors=0;words=s->count*16;
        for(n=0;n<words;n++) if(*(volatile u16*)VDP_DATA_PORT!=expected[n]) errors++;
        s->readback_errors+=errors;s->readback_words+=words;
        if(s->readback_errors) {s->error=1;return MD_Z80_PSG_FAULT;}
    }
    s->last_kind=s->kind;
    if(s->kind==1) s->pattern_cursor+=s->count;else s->map_row++;
    s->kind=0;return MD_Z80_PSG_OK;
}
