#include <string.h>
#include "include/gaw_video.h"

/* Video hardware shadow shared by native code and the reference CPU. */
static uint8_t vdp_ctrl_latch, vdp_ctrl_low;
static uint16_t vdp_addr;
static uint8_t vdp_code;
static uint8_t vdp_regs[16], vdp_vram[0x4000], vdp_cram[0x20], vdp_readbuf, vdp_status;
static uint8_t vdp_tile_dirty[512];
static uint16_t dirty_low,dirty_high;
static uint8_t vdp_name_dirty, vdp_sat_dirty;
static uint32_t vdp_name_rows_dirty;
static uint8_t vdp_sprite_status_dirty, vdp_sprite_status_cache;

static void mark_tile_dirty(unsigned tile){
    if(vdp_tile_dirty[tile])return;
    vdp_tile_dirty[tile]=1;
    if(dirty_low>dirty_high){dirty_low=dirty_high=(uint16_t)tile;return;}
    if(tile<dirty_low)dirty_low=(uint16_t)tile;
    if(tile>dirty_high)dirty_high=(uint16_t)tile;
}

static void vdp_ctrl(uint8_t v){ if(!vdp_ctrl_latch){vdp_ctrl_low=v;vdp_ctrl_latch=1;return;} vdp_ctrl_latch=0; vdp_code=(uint8_t)(v>>6); if(vdp_code==2){unsigned r=v&15u;if(vdp_regs[r]==vdp_ctrl_low)return;vdp_regs[r]=vdp_ctrl_low;if(r==2u){vdp_name_dirty=1;vdp_name_rows_dirty=0x0FFFFFFFu;}if(r==0u||r==1u||r==5u||r==6u){vdp_sat_dirty=1;vdp_sprite_status_dirty=1;}return;} vdp_addr=(uint16_t)(((uint16_t)(v&0x3Fu)<<8)|vdp_ctrl_low); if(vdp_code==0){vdp_readbuf=vdp_vram[vdp_addr&0x3FFFu];vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);} }
static void vdp_data_w(uint8_t v){vdp_ctrl_latch=0;if(vdp_code==3)vdp_cram[vdp_addr&31u]=v;else {uint16_t a=(uint16_t)(vdp_addr&0x3FFFu);if(vdp_vram[a]!=v){vdp_vram[a]=v;mark_tile_dirty(a>>5);vdp_sprite_status_dirty=1;uint16_t nt=(uint16_t)((vdp_regs[2]&0x0Eu)<<10);if(a>=nt&&a<(uint16_t)(nt+0x0700u)){vdp_name_dirty=1;vdp_name_rows_dirty|=(uint32_t)1u<<((a-nt)>>6);}uint16_t sat=(uint16_t)((vdp_regs[5]&0x7Eu)<<7);if(a>=sat&&a<(uint16_t)(sat+0x0100u))vdp_sat_dirty=1;}}vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);}
static uint8_t vdp_data_r(void){uint8_t v=vdp_readbuf;vdp_readbuf=vdp_vram[vdp_addr&0x3FFFu];vdp_addr=(uint16_t)((vdp_addr+1u)&0x3FFFu);vdp_ctrl_latch=0;return v;}
void gaw_sms_vdp_control_write(uint8_t value){vdp_ctrl(value);}
void gaw_sms_vdp_data_write(uint8_t value){vdp_data_w(value);}
/* Preserve scalar port state/dirty semantics while testing/copying one pattern
 * fragment at a time. Name rows and SAT boundaries are pattern-aligned too. */
void gaw_sms_vdp_data_write_block(const uint8_t *source,unsigned count){
    if(!count)return;
    uintptr_t p=(uintptr_t)source;
    if((p>=(uintptr_t)vdp_vram&&p<(uintptr_t)(vdp_vram+sizeof vdp_vram))||
       (p>=(uintptr_t)vdp_cram&&p<(uintptr_t)(vdp_cram+sizeof vdp_cram))){
        /* A source inside the shadow can observe earlier writes in this block. */
        while(count--)vdp_data_w(*source++);
        return;
    }
    vdp_ctrl_latch=0;
    uint16_t nt=(uint16_t)((vdp_regs[2]&0x0Eu)<<10);
    uint16_t sat=(uint16_t)((vdp_regs[5]&0x7Eu)<<7);
    while(count){
        uint16_t a=vdp_addr;
        unsigned n=32u-(a&31u);if(n>count)n=count;
        if(vdp_code==3u)memcpy(vdp_cram+(a&31u),source,n);
        else if(memcmp(vdp_vram+a,source,n)!=0){
            memcpy(vdp_vram+a,source,n);
            mark_tile_dirty(a>>5);vdp_sprite_status_dirty=1;
            if(a>=nt&&a<(uint16_t)(nt+0x700u)){
                vdp_name_dirty=1;vdp_name_rows_dirty|=(uint32_t)1u<<((a-nt)>>6);
            }
            if(a>=sat&&a<(uint16_t)(sat+0x100u))vdp_sat_dirty=1;
        }
        vdp_addr=(uint16_t)((a+n)&0x3FFFu);source+=n;count-=n;
    }
}
uint8_t gaw_sms_vdp_data_read(void){return vdp_data_r();}

const uint8_t *gaw_sms_vram(void){return vdp_vram;}
const uint8_t *gaw_sms_cram(void){return vdp_cram;}
const uint8_t *gaw_sms_vdp_regs(void){return vdp_regs;}
int gaw_sms_take_tile_dirty(unsigned tile){if(tile>=512||!vdp_tile_dirty[tile])return 0;vdp_tile_dirty[tile]=0;return 1;}
int gaw_sms_take_next_tile_dirty(void){
    while(dirty_low<=dirty_high){
        unsigned tile=dirty_low++;
        if(vdp_tile_dirty[tile]){vdp_tile_dirty[tile]=0;return (int)tile;}
    }
    return -1;
}
void gaw_sms_mark_all_tiles_dirty(void){memset(vdp_tile_dirty,1,sizeof vdp_tile_dirty);dirty_low=0;dirty_high=511;}

int gaw_sms_take_name_dirty(void){int v=vdp_name_dirty;vdp_name_dirty=0;vdp_name_rows_dirty=0;return v;}
uint32_t gaw_sms_take_name_rows_dirty(void){uint32_t v=vdp_name_rows_dirty;vdp_name_dirty=0;vdp_name_rows_dirty=0;return v;}
int gaw_sms_take_sat_dirty(void){int v=vdp_sat_dirty;vdp_sat_dirty=0;return v;}

void gaw_video_reset(void){
    memset(vdp_regs,0,sizeof vdp_regs);memset(vdp_vram,0,sizeof vdp_vram);
    memset(vdp_cram,0,sizeof vdp_cram);memset(vdp_tile_dirty,1,sizeof vdp_tile_dirty);
    dirty_low=0;dirty_high=511;
    vdp_name_dirty=vdp_sat_dirty=1;vdp_name_rows_dirty=0x0FFFFFFFu;vdp_ctrl_latch=0;vdp_ctrl_low=0;
    vdp_addr=0;vdp_code=0;vdp_status=0;vdp_readbuf=0;
    vdp_sprite_status_dirty=1;vdp_sprite_status_cache=0;
}
uint8_t gaw_video_status_read(void){uint8_t s=vdp_status;vdp_status=0;vdp_ctrl_latch=0;return s;}
void gaw_video_status_pending(uint8_t flags){vdp_status|=flags;}
void gaw_video_vblank_pending(void){
    if(vdp_sprite_status_dirty){
        vdp_sprite_status_cache=gaw_video_sprite_status(vdp_vram,vdp_regs);
        vdp_sprite_status_dirty=0;
    }
    gaw_video_status_pending((uint8_t)(0x80u|vdp_sprite_status_cache));
}
void gaw_video_write_at(uint16_t address,uint8_t value){vdp_addr=address&0x3FFFu;vdp_code=1;vdp_data_w(value);}
