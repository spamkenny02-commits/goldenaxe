#include "gaw_assets.h"
#include "gaw_ui.h"
#include <stdint.h>
#include "gaw_core.h"
#include "gaw_platform.h"
#include "gaw_video.h"
#include "gaw_md_video.h"
#include "gaw_ram.h"

#define VDP_DATA (*(volatile uint16_t*)0xC00000)
#define VDP_CTRL (*(volatile uint16_t*)0xC00004)
#define VDP_CTRL32 (*(volatile uint32_t*)0xC00004)
#define PSG      (*(volatile uint8_t*)0xC00011)
#define IO_VER   (*(volatile uint8_t*)0xA10001)
#define JOY1_DATA (*(volatile uint8_t*)0xA10003)
#define JOY1_CTRL (*(volatile uint8_t*)0xA10009)
#define SRAM_CTRL (*(volatile uint8_t*)0xA130F1)
#define Z80_BUS (*(volatile uint8_t*)0xA11100)
#define Z80_RESET (*(volatile uint8_t*)0xA11200)
#define SRAM8(o) (*(volatile uint8_t*)(uintptr_t)(0x200001u+((uint32_t)(o)<<1)))

static uint8_t entropy, md_start_held;
/* Hardware diagnostics read by the private emulator check. */
volatile uint32_t gaw_md_vblank_count, gaw_md_async_vblank_count, gaw_md_line_count;
static inline void irq_mask(uint16_t status){__asm__ volatile("move.w %0,%%sr"::"d"(status):"cc","memory");}
static inline void vdp_reg(unsigned r,uint8_t v){VDP_CTRL=(uint16_t)(0x8000u|((r&31u)<<8)|v);}
uint32_t gaw_md_vdp_command(uint16_t a,uint32_t code){
    return code|((uint32_t)(a&0x3FFFu)<<16)|((uint32_t)(a>>14)&3u);
}
static inline void vdp_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0x40000000u);}
static inline void cram_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0xC0000000u);}
static inline void vsram_addr_write(uint16_t a){VDP_CTRL32=gaw_md_vdp_command(a,0x40000010u);}
static void upload_tile(unsigned t,const uint8_t *v){
    const uint8_t *p=v+t*32u;
    vdp_addr_write((uint16_t)(t*32u));
    for(unsigned y=0;y<8u;++y){
        uint32_t row=gaw_md_pattern_row(p[0],p[1],p[2],p[3]);
        VDP_DATA=(uint16_t)(row>>16);VDP_DATA=(uint16_t)row;p+=4;
    }
}
static void init_sms_viewport_mask(void){
    /* SMS background pixel zero is opaque colour, but never hides a sprite.
       Plane B supplies palette-zero colour below the SMS pattern in Plane A.
       Two MD-only solid tiles also mask the 192..223 viewport extension. */
    vdp_addr_write(0xA000); for(unsigned i=0;i<16u;++i) VDP_DATA=0x1111u; /* tile $500, colour 1 */
    vdp_addr_write(0xA020);for(unsigned i=0;i<16u;++i)VDP_DATA=0x2222u; /* tile $501, colour 2 */
    vdp_addr_write(0xE000);for(unsigned i=0;i<32u*32u;++i)VDP_DATA=0xC501u; /* pri, pal2, tile $501 */
    vdp_addr_write(0x8000);for(unsigned i=0;i<32u*32u;++i)VDP_DATA=0x4500u; /* pal2, tile $500 */
    vdp_reg(3,0x38);  /* Window table $E000 in H32. */
    vdp_reg(17,0);    /* No horizontal Window; vertical selection covers the bottom. */
    vdp_reg(18,0x98); /* Window from row 24 to the bottom. */
}
static void sync_scroll(const uint8_t *r){
    uint8_t mode=0;
    if(r[0]&0x40u) mode|=3u;       /* SMS: top 16 lines do not H-scroll. */
    if(r[0]&0x80u) mode|=4u;       /* SMS: rightmost 8 columns do not V-scroll. */
    vdp_reg(11,mode);

    vdp_addr_write(0xB000);
    if(mode&3u){
        for(unsigned y=0;y<224u;++y){uint16_t h=(uint16_t)(y<16u?0u:r[8]);VDP_DATA=h;VDP_DATA=h;}
    }else{VDP_DATA=r[8];VDP_DATA=r[8];}

    vsram_addr_write(0);
    if(mode&4u){
        for(unsigned col=0;col<16u;++col){uint16_t s=(uint16_t)(col<12u?r[9]:0u);VDP_DATA=s;VDP_DATA=s;}
    }else{VDP_DATA=r[9];VDP_DATA=r[9];}
}
static void sync_sms_shadow(void){const uint8_t*v=gaw_sms_vram();const uint8_t*c=gaw_sms_cram();const uint8_t*r=gaw_sms_vdp_regs();vdp_reg(0,(uint8_t)(0x04u|(r[0]&0x30u)));vdp_reg(1,(uint8_t)(0x24u|(r[1]&0x40u)));vdp_reg(10,r[10]);vdp_reg(7,(uint8_t)(0x10u|(r[7]&0x0Fu)));sync_scroll(r);for(int t=gaw_sms_take_next_tile_dirty();t>=0;t=gaw_sms_take_next_tile_dirty())upload_tile((unsigned)t,v);
    cram_addr_write(0);for(unsigned i=0;i<32;++i)VDP_DATA=gaw_md_color(c[i]);
    cram_addr_write(0x42);VDP_DATA=gaw_md_color(c[0]);
    cram_addr_write(0x62);VDP_DATA=gaw_md_color(c[16]);
    cram_addr_write(0x44);VDP_DATA=gaw_md_color(c[16u+(r[7]&0x0Fu)]);
    uint32_t rows=gaw_sms_take_name_rows_dirty();
    uint16_t nt=(uint16_t)((r[2]&0x0Eu)<<10);
    for(unsigned y=0;rows;++y,rows>>=1)if(rows&1u){
        vdp_addr_write((uint16_t)(0xC000u+y*64u));
        for(unsigned x=0;x<32u;++x){unsigned o=(nt+2u*(y*32u+x))&0x3FFFu;uint16_t s=(uint16_t)v[o]|((uint16_t)v[(o+1u)&0x3FFFu]<<8);VDP_DATA=gaw_md_descriptor(s);}
        vdp_addr_write((uint16_t)(0x8000u+y*64u));
        for(unsigned x=0;x<32u;++x){unsigned o=(nt+2u*(y*32u+x))&0x3FFFu;uint16_t s=(uint16_t)v[o]|((uint16_t)v[(o+1u)&0x3FFFu]<<8);VDP_DATA=gaw_md_zero_descriptor(s);}
    }
    if(gaw_sms_take_sat_dirty()){uint16_t sat=(uint16_t)((r[5]&0x7Eu)<<7);vdp_addr_write(0xD800);unsigned out=0;int tall=(r[1]&0x02u)!=0;int shift_left=(r[0]&0x08u)!=0;uint16_t sprite_base=(r[6]&0x04u)?0x100u:0u;for(unsigned i=0;i<64&&out<64;++i){uint8_t sy=v[(sat+i)&0x3FFFu];if(sy==0xD0)break;uint8_t sx=v[(sat+0x80u+i*2u)&0x3FFFu];uint16_t tile=(uint16_t)(sprite_base|v[(sat+0x81u+i*2u)&0x3FFFu]);if(tall)tile&=0x01FEu;VDP_DATA=gaw_md_sprite_y(sy);VDP_DATA=(uint16_t)(((tall?1u:0u)<<8)|((out+1u)&0x7Fu));VDP_DATA=(uint16_t)(0x2000u|tile);VDP_DATA=(uint16_t)((uint16_t)(sx+128u-(shift_left?8u:0u))&0x03FFu);++out;}if(out){uint16_t a=(uint16_t)(0xD800u+(out-1u)*8u+2u);vdp_addr_write(a);VDP_DATA=(uint16_t)((tall?1u:0u)<<8);}else{vdp_addr_write(0xD800);for(unsigned i=0;i<4u;++i)VDP_DATA=0;}} }

void gaw_platform_init(void){irq_mask(0x2700);entropy=0x5A;md_start_held=0;Z80_BUS=1;Z80_RESET=0;SRAM_CTRL=0x01;JOY1_CTRL=0x40;JOY1_DATA=0x40;vdp_reg(0,0x04);vdp_reg(1,0x24);vdp_reg(2,0x30);vdp_reg(3,0x2C);vdp_reg(4,0x04);vdp_reg(5,0x6C);vdp_reg(7,0);vdp_reg(10,0xFF);vdp_reg(11,0);vdp_reg(12,0x00);vdp_reg(13,0x2C);vdp_reg(15,2);vdp_reg(16,0x00);vdp_reg(17,0);vdp_reg(18,0);init_sms_viewport_mask();gaw_sms_mark_all_tiles_dirty();gaw_ram_write8(0xDE03u,(uint8_t)(IO_VER&0x40u?0:0x80));}
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
void gaw_md_vblank_irq(void){
    (void)VDP_CTRL;++gaw_md_vblank_count;
    if(!gaw_ram_read8(RAM_VBLANK_WAIT_FLAG))++gaw_md_async_vblank_count;
    gaw_vblank_tick(gaw_platform_read_pad_sms_bits());
}
void gaw_md_line_irq(void){
    (void)VDP_CTRL;++gaw_md_line_count;gaw_irq_service(0);
    switch(gaw_ram_read16le(0xC02Cu)){
        case 0x0263:vdp_reg(0,(uint8_t)(0x04u|(gaw_sms_vdp_regs()[0]&0x30u)));break;
        case 0x0275:vdp_addr_write(0xB000);VDP_DATA=0;VDP_DATA=0;break;
        case 0x0280:
            cram_addr_write(0x20);VDP_DATA=0;
            cram_addr_write(0x62);VDP_DATA=0;
            if((gaw_sms_vdp_regs()[7]&0x0Fu)==0){cram_addr_write(0x44);VDP_DATA=0;}
            break;
    }
}
void gaw_platform_wait_vblank(void){
    irq_mask(0x2300);
    while(*(volatile uint8_t*)gaw_ram_ptr(RAM_VBLANK_WAIT_FLAG)){}
    /* A line handler changes VDP addresses; block level 4 during uploads.
       Level 6 remains enabled for asynchronous sound/timer updates. */
    irq_mask(0x2400);sync_sms_shadow();irq_mask(0x2300);
}
void gaw_platform_sound_write(uint8_t port,uint8_t value){if(port==0x7Fu)PSG=value;}
uint8_t gaw_platform_entropy8(void){uint8_t h=*(volatile uint8_t*)0xC00008;entropy=(uint8_t)(entropy*33u+17u+h);return entropy;}
void gaw_platform_entity_resource_load(uint8_t id){gaw_assets_load_item(id,0x7780u);}
void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot){gaw_assets_load_map_entity(type,gfx_slot);}
void gaw_platform_world_rebuilt(void){gaw_ui_upload_name_table();}
void gaw_platform_inventory_refresh(void){gaw_assets_update_inventory();}
void gaw_platform_world_message(uint16_t resource,uint8_t saved_cell){(void)saved_cell;gaw_ui_show_message(resource);}
uint8_t gaw_platform_sram_read(uint16_t o){return SRAM8(o&0x7FFFu);}void gaw_platform_sram_write(uint16_t o,uint8_t v){SRAM8(o&0x7FFFu)=v;}
