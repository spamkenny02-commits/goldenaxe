#include "gaw_assets.h"
#include "gaw_ui.h"
#include <stdint.h>
#include "gaw_core.h"
#include "gaw_platform.h"
#include "gaw_video.h"

#define VDP_DATA (*(volatile uint16_t*)0xC00000)
#define VDP_CTRL (*(volatile uint16_t*)0xC00004)
#define VDP_CTRL32 (*(volatile uint32_t*)0xC00004)
#define PSG      (*(volatile uint8_t*)0xC00011)
#define IO_VER   (*(volatile uint8_t*)0xA10001)
#define JOY1_DATA (*(volatile uint8_t*)0xA10003)
#define JOY1_CTRL (*(volatile uint8_t*)0xA10009)
#define SRAM_CTRL (*(volatile uint8_t*)0xA130F1)
#define SRAM8(o) (*(volatile uint8_t*)(uintptr_t)(0x200001u+((uint32_t)(o)<<1)))

static uint8_t entropy, md_start_held;
static inline void vdp_reg(unsigned r,uint8_t v){VDP_CTRL=(uint16_t)(0x8000u|((r&31u)<<8)|v);}
uint32_t gaw_md_vdp_command(uint16_t a,uint32_t code){
    return code|((uint32_t)(a&0x3FFFu)<<16)|((uint32_t)(a>>14)&3u);
}
static inline void vdp_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0x40000000u);}
static inline void cram_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0xC0000000u);}
static inline void vsram_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0x40000010u);}
static uint16_t sms_color(uint8_t c){unsigned r=(c&3u)*2u,g=((c>>2)&3u)*2u,b=((c>>4)&3u)*2u;return (uint16_t)((b<<9)|(g<<5)|(r<<1));}
static uint16_t sms_name_to_md(uint16_t s){uint16_t m=(uint16_t)(s&0x01FFu);m|=(uint16_t)((s&0x0200u)<<2);m|=(uint16_t)((s&0x0400u)<<2);m|=(uint16_t)((s&0x0800u)<<2);m|=(uint16_t)((s&0x1000u)<<3);return m;}
static void upload_tile(unsigned t,const uint8_t *v){uint16_t words[16];const uint8_t*p=v+t*32u;for(unsigned y=0;y<8;++y){uint8_t a=p[y*4],b=p[y*4+1],c=p[y*4+2],d=p[y*4+3];uint32_t row=0;for(unsigned x=0;x<8;++x){unsigned bit=7u-x;unsigned px=((a>>bit)&1u)|(((b>>bit)&1u)<<1)|(((c>>bit)&1u)<<2)|(((d>>bit)&1u)<<3);row=(row<<4)|px;}words[y*2]=(uint16_t)(row>>16);words[y*2+1]=(uint16_t)row;}vdp_addr_write((uint16_t)(t*32u));for(unsigned i=0;i<16;++i)VDP_DATA=words[i];}
static void init_sms_viewport_mask(void){
    /* SMS mode-4 gameplay is 256x192.  MD V28 is 256x224, so reserve a
       MD-only solid tile and use the Window plane to cover rows 24..27. */
    vdp_addr_write(0xA000); for(unsigned i=0;i<16u;++i) VDP_DATA=0x1111u; /* tile $500, colour 1 */
    vdp_addr_write(0xE000); for(unsigned i=0;i<32u*32u;++i) VDP_DATA=0xC500u; /* pri, pal2, tile $500 */
    vdp_reg(3,0x38);  /* Window table $E000 in H32. */
    vdp_reg(17,0x80); /* Window from x=0 to the right edge. */
    vdp_reg(18,0x98); /* Window from row 24 to the bottom. */
}
static void sync_scroll(const uint8_t *r){
    uint8_t mode=0;
    if(r[0]&0x40u) mode|=3u;       /* SMS: top 16 lines do not H-scroll. */
    if(r[0]&0x80u) mode|=4u;       /* SMS: rightmost 8 columns do not V-scroll. */
    vdp_reg(11,mode);

    vdp_addr_write(0xB000);
    if(mode&3u){
        for(unsigned y=0;y<224u;++y){ VDP_DATA=(uint16_t)(y<16u?0u:r[8]); VDP_DATA=0; }
    }else{ VDP_DATA=r[8]; VDP_DATA=0; }

    vsram_addr_write(0);
    if(mode&4u){
        for(unsigned col=0;col<16u;++col){ VDP_DATA=(uint16_t)(col<12u?r[9]:0u); VDP_DATA=0; }
    }else{ VDP_DATA=r[9]; VDP_DATA=0; }
}
static void sync_sms_shadow(void){const uint8_t*v=gaw_sms_vram();const uint8_t*c=gaw_sms_cram();const uint8_t*r=gaw_sms_vdp_regs();vdp_reg(0,(uint8_t)(0x04u|(r[0]&0x20u)));vdp_reg(1,(uint8_t)(0x04u|(r[1]&0x40u)));vdp_reg(7,(uint8_t)(0x10u|(r[7]&0x0Fu)));sync_scroll(r);for(unsigned t=0;t<512;++t)if(gaw_sms_take_tile_dirty(t))upload_tile(t,v);
    cram_addr_write(0);for(unsigned i=0;i<32;++i)VDP_DATA=sms_color(c[i]);cram_addr_write(0x42);VDP_DATA=sms_color(c[16u+(r[7]&0x0Fu)]);
    if(gaw_sms_take_name_dirty()){uint16_t nt=(uint16_t)((r[2]&0x0Eu)<<10);vdp_addr_write(0xC000);for(unsigned y=0;y<28;++y)for(unsigned x=0;x<32;++x){unsigned o=(nt+2u*(y*32u+x))&0x3FFFu;uint16_t s=(uint16_t)v[o]|((uint16_t)v[(o+1u)&0x3FFFu]<<8);VDP_DATA=sms_name_to_md(s);}}
    if(gaw_sms_take_sat_dirty()){uint16_t sat=(uint16_t)((r[5]&0x7Eu)<<7);vdp_addr_write(0xD800);unsigned out=0;int tall=(r[1]&0x02u)!=0;int shift_left=(r[0]&0x08u)!=0;uint16_t sprite_base=(r[6]&0x04u)?0x100u:0u;for(unsigned i=0;i<64&&out<64;++i){uint8_t sy=v[(sat+i)&0x3FFFu];if(sy==0xD0)break;uint8_t sx=v[(sat+0x80u+i*2u)&0x3FFFu];uint16_t tile=(uint16_t)(sprite_base|v[(sat+0x81u+i*2u)&0x3FFFu]);if(tall)tile&=0x01FEu;VDP_DATA=(uint16_t)((uint16_t)(sy+1u+128u)&0x03FFu);VDP_DATA=(uint16_t)(((tall?1u:0u)<<8)|((out+1u)&0x7Fu));VDP_DATA=(uint16_t)(0x2000u|tile);VDP_DATA=(uint16_t)((uint16_t)(sx+128u-(shift_left?8u:0u))&0x03FFu);++out;}if(out){uint16_t a=(uint16_t)(0xD800u+(out-1u)*8u+2u);vdp_addr_write(a);VDP_DATA=(uint16_t)((tall?1u:0u)<<8);}} }

void gaw_platform_init(void){entropy=0x5A;md_start_held=0;SRAM_CTRL=0x01;JOY1_CTRL=0x40;JOY1_DATA=0x40;vdp_reg(0,0x04);vdp_reg(1,0x04);vdp_reg(2,0x30);vdp_reg(3,0x2C);vdp_reg(4,0x07);vdp_reg(5,0x6C);vdp_reg(7,0);vdp_reg(10,0);vdp_reg(11,0);vdp_reg(12,0x00);vdp_reg(13,0x2C);vdp_reg(15,2);vdp_reg(16,0x00);vdp_reg(17,0);vdp_reg(18,0);init_sms_viewport_mask();gaw_sms_mark_all_tiles_dirty();}
uint8_t gaw_platform_read_pad_sms_bits(void){
    JOY1_DATA=0x40; uint8_t hi=JOY1_DATA;
    JOY1_DATA=0x00; (void)JOY1_DATA; uint8_t lo=JOY1_DATA;
    JOY1_DATA=0x40;
    uint8_t held=(uint8_t)(~hi)&0x3Fu;
    if((lo&0x10u)==0) held|=0x10u; /* A is an alternate SMS button 1. */
    uint8_t start=(uint8_t)((lo&0x20u)==0);
    if(start&&!md_start_held) gaw_nmi_pause();
    md_start_held=start;
    return held;
}
void gaw_platform_wait_vblank(void){while(VDP_CTRL&0x0008u){}while(!(VDP_CTRL&0x0008u)){}sync_sms_shadow();gaw_vblank_tick(gaw_platform_read_pad_sms_bits());}
void gaw_platform_audio_command(uint8_t command){PSG=command;}
uint8_t gaw_platform_entropy8(void){uint8_t h=*(volatile uint8_t*)0xC00008;entropy=(uint8_t)(entropy*33u+17u+h);return entropy;}
void gaw_platform_entity_resource_load(uint8_t id){gaw_assets_load_item(id,0x7780u);}void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot){(void)type;(void)gfx_slot;}void gaw_platform_world_rebuilt(void){gaw_ui_upload_name_table();}void gaw_platform_world_scroll_begin(void){}void gaw_platform_world_scroll_end(void){}void gaw_platform_inventory_refresh(void){}void gaw_platform_player_special_effect(uint8_t id){(void)id;}void gaw_platform_show_world_map(void){}void gaw_platform_world_message(uint16_t resource,uint8_t saved_cell){(void)saved_cell;gaw_ui_show_message(resource);}void gaw_platform_player_transition_frame(void){}
uint8_t gaw_platform_sram_read(uint16_t o){return SRAM8(o&0x7FFFu);}void gaw_platform_sram_write(uint16_t o,uint8_t v){SRAM8(o&0x7FFFu)=v;}
