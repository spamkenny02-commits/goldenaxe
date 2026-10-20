#include "md_sms_sprite8_stream.h"
u8 md_sms_sprite8_stream_begin(MdSmsSprite8Stream *s,const u8 *sat,const u32 *patterns,
                               u8 r0,u8 r1,u8 r6,u16 base,u8 verify)
{
    u16 address=VDP_getSpriteListAddress();u32 first=(u32)base*32;
    if(!s || !sat || !patterns || ((u32)patterns&1) || (s->ready && !s->done) ||
       VDP_isEnable() || VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224 ||
       (address&511) || address>65024 || (first<(u32)address+512 && address<first+2048)) return MD_Z80_PSG_INVALID;
    if(source_sms_sprite8_prepare(&s->frame,sat,r0,r1,r6,base)) return MD_Z80_PSG_INVALID;
    s->patterns=patterns;s->sat_address=address;s->sprite_cursor=s->sat_cursor=s->address=s->count=0;
    s->done=s->error=s->kind=s->last_kind=0;s->job.ready=0;s->ready=1;s->verify=verify;
    s->readback_words=s->readback_errors=0;return MD_Z80_PSG_OK;
}
u8 md_sms_sprite8_stream_step(MdSmsSprite8Stream *s,MdZ80PsgMailbox *mailbox)
{
    u16 n,words,expected,errors;u8 status;
    if(!s || !mailbox) return MD_Z80_PSG_INVALID;
    if(s->error) return MD_Z80_PSG_FAULT;
    if(mailbox->stamp.error) {s->error=1;return MD_Z80_PSG_FAULT;}
    if(!s->ready || s->done) return MD_Z80_PSG_WAIT;
    if(VDP_isEnable() || VDP_getScreenWidth()!=256 || VDP_getScreenHeight()!=224 ||
       VDP_getSpriteListAddress()!=s->sat_address) return MD_Z80_PSG_INVALID;
    if(!mailbox->stamp.ready) return MD_Z80_PSG_WAIT;
    if(!(mailbox->stamp.ready&MD_Z80_VIDEO_SPAN_REFRESH_CAP)) return MD_Z80_PSG_INVALID;
    if(!s->kind) {
        if(s->sprite_cursor<s->frame.count) {
            s->count=s->frame.count-s->sprite_cursor;if(s->count>4) s->count=4;
            for(n=0;n<s->count;n++) if(source_sms_sprite8_tile(&s->frame,s->patterns,s->sprite_cursor+n,s->payload+n*8)) {s->error=1;return MD_Z80_PSG_FAULT;}
            s->address=(s->frame.tile_base+s->sprite_cursor)*32;s->kind=1;
            status=md_z80_video_span_prepare_refresh(&s->job,s->payload,s->address/32,s->count);
        } else {
            s->count=4;s->address=s->sat_address+s->sat_cursor*32;s->kind=2;
            status=md_z80_video_span_prepare_refresh(&s->job,(const u32*)(s->frame.sat+s->sat_cursor*16),s->address/32,4);
        }
        if(status) {s->error=1;return status;}
    }
    status=md_z80_video_span_try_hidden(mailbox,&s->job);
    if(status!=MD_Z80_PSG_OK) {if(status==MD_Z80_PSG_FAULT) s->error=1;return status;}
    if(s->verify) {
        *(volatile u32*)VDP_CTRL_PORT=VDP_READ_VRAM_ADDR(s->address);errors=0;words=s->count*16;
        for(n=0;n<words;n++) {
            expected=s->kind==1?(n&1?(u16)s->payload[n/2]:(u16)(s->payload[n/2]>>16)):s->frame.sat[s->sat_cursor*16+n];
            if(*(volatile u16*)VDP_DATA_PORT!=expected) errors++;
        }
        s->readback_words+=words;s->readback_errors+=errors;
        if(errors) {s->error=1;return MD_Z80_PSG_FAULT;}
    }
    s->last_kind=s->kind;if(s->kind==1) s->sprite_cursor+=s->count;else s->sat_cursor+=4;
    s->kind=0;if(s->sat_cursor==16) s->done=1;
    return MD_Z80_PSG_OK;
}
