#include <string.h>
#include "include/gaw_world.h"
#include "include/gaw_core.h"
#include "include/gaw_entity.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_world_progress.h"
#include "include/gaw_ui.h"
#include "include/gaw_assets.h"
#include "include/gaw_video.h"

#define R8(a) gaw_ram_read8((a))
#define W8(a,v) gaw_ram_write8((a),(v))

static const uint8_t world_map_bank_08[0x4000] = {
#include "world_map_bank_08.inc"
};
static const uint8_t world_map_bank_09[0x4000] = {
#include "world_map_bank_09.inc"
};
static const uint8_t world_map_bank_10[0x4000] = {
#include "world_map_bank_10.inc"
};
static const uint8_t world_map_bank_11[0x4000] = {
#include "world_map_bank_11.inc"
};

static const uint8_t *world_bank(unsigned index) {
    switch (index) {
        case 0: return world_map_bank_08;
        case 1: return world_map_bank_09;
        case 2: return world_map_bank_10;
        default:return world_map_bank_11;
    }
}

/* $175F. C040 is a layer/environment selector used by progression and assets. */
void gaw_world_select_layer(void) {
    uint8_t layer;
    if (R8(0xC0BA)!=0) layer=2;
    else {
        uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID);
        if (cell<0x10u || (cell&0x0Fu)==0x0Fu) layer=1;
        else layer=0;
    }
    W8(0xC040,layer);
}

/* Exact data semantics of $0C00 for C=1: positive commands repeat one byte;
   high-bit commands copy (cmd&$7F) literal bytes; zero terminates. */
static bool world_decompress_map(uint16_t id) {
    if (id>=512u) return false;
    uint16_t doubled=(uint16_t)(id<<1);
    unsigned bi=(unsigned)(doubled>>8); /* bank 8 + bi */
    const uint8_t *bank=world_bank(bi);
    unsigned po=(unsigned)(doubled&0xFFu);
    uint16_t cpu=(uint16_t)bank[po] | ((uint16_t)bank[po+1u]<<8);
    if (cpu<0x8000u || cpu>=0xC000u) return false;
    unsigned p=(unsigned)(cpu-0x8000u);
    uint16_t dst=0xDC00u;
    unsigned produced=0;
    while (p<0x4000u) {
        uint8_t cmd=bank[p++];
        if (cmd==0) return produced==160u;
        if (cmd&0x80u) {
            unsigned n=(unsigned)(cmd&0x7Fu);
            if (p+n>0x4000u || produced+n>160u) return false;
            while (n--) { W8(dst++,bank[p++]); ++produced; }
        } else {
            unsigned n=cmd;
            if (p>=0x4000u || produced+n>160u) return false;
            uint8_t v=bank[p++];
            while (n--) { W8(dst++,v); ++produced; }
        }
    }
    return false;
}

/* $1A30/$1A09 RAM-visible post-load work. */
static void world_post_load_aux(void) {
    if (R8(0xC040)==0) {
        uint16_t src=R8(0xC0AC)==0 ? 0xC998u : 0xC080u;
        memcpy(gaw_ram_ptr(0xCAC0),gaw_ram_ptr(src),8);
        memcpy(gaw_ram_ptr(0xCAF0),gaw_ram_ptr(R8(0xC0AC)==0?src:0xC088u),8);
        if (R8(0xC0AC)!=0) {
            uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID);
            if (cell==0x96u || cell==0xAAu || cell==0xCBu) {
                (void)gaw_world_progress_test_and_set();
                gaw_world_progress_restore_for_current_cell();
            }
        }
    }
    if (gaw_ram_read16le(RAM_WORLD_CELL_ID)==0x00BFu) {
        static const uint8_t key[3]={0xA3,0x2C,0xAA};
        static const uint8_t val[3]={0x2A,0x28,0x28};
        uint8_t sub=(uint8_t)gaw_ram_read16le(0xC0BB);
        for (unsigned i=0;i<3;++i) if (sub==key[i]) { W8(0xDC28,val[i]); break; }
    }
}

bool gaw_world_load_current_cell(void) {
    gaw_world_select_layer();
    if (!world_decompress_map(gaw_ram_read16le(RAM_WORLD_CELL_ID))) return false;
    gaw_world_progress_restore_for_current_cell();
    world_post_load_aux();
    W8(0xDD00,0);
    gaw_ram_write16le(0xC034,0xDD00);
    return true;
}

/* $22E2 + $2279. */
void gaw_world_expand_metatiles(void) {
    uint16_t dst=0xD600u;
    for (unsigned row=0;row<20;++row) {
        for (unsigned col=0;col<32;++col) {
            unsigned cell=((row&~1u)<<3)+(col>>1);
            uint8_t tile=R8((uint16_t)(0xDC00u+cell));
            unsigned q=((row&1u)?4u:0u)+((col&1u)?2u:0u);
            uint16_t src=(uint16_t)(0xC900u+(unsigned)tile*8u+q);
            W8(dst++,R8(src));
            W8(dst++,R8((uint16_t)(src+1u)));
        }
    }
}

void gaw_world_finalize_transition(void) {
    /* $5E90 = $1976 + $1DE2. Descriptor expansion, HUD construction and
       status-template RAM are native; only the physical VDP upload remains
       behind the platform callback. */
    gaw_world_progress_restore_for_current_cell();
    gaw_world_expand_metatiles();
    gaw_hud_rebuild_full();
    /* $229C begins with $0B95: preserve the VBlank boundary as well as the
       eventual platform upload, because C02F/input timers advance here. */
    gaw_wait_frame();
    gaw_platform_world_rebuilt();
    static const uint8_t status_template[16]={0x00,0x00,0x1B,0x3F,0x1F,0x06,0x38,0x30,0x03,0x0D,0x08,0x14,0x3C,0x30,0x2A,0x00};
    memcpy(gaw_ram_ptr(0xDCB0u),status_template,sizeof status_template);
    gaw_hud_update_status_descriptor();
}

static uint16_t descriptor_addr(const GawEntity *e, int8_t yoff, int8_t xoff) {
    uint8_t x=(uint8_t)(e->raw[0x11]+(uint8_t)xoff);
    uint8_t y=(uint8_t)(e->raw[0x13]+(uint8_t)yoff);
    uint16_t off=(uint16_t)((uint16_t)(x&0xF8u)<<3);
    off=(uint16_t)(off+(uint16_t)(((uint8_t)(y>>2))&0x3Eu));
    return (uint16_t)(0xD600u+off);
}

static bool descriptor_is_a0(const GawEntity *e, int8_t yoff, int8_t xoff) {
    uint16_t a=descriptor_addr(e,yoff,xoff);
    uint8_t high=R8((uint16_t)(a+1u));
    return (high&0xE0u)==0xA0u;
}

static uint8_t progress_mask(uint8_t bit) { return (uint8_t)(1u<<(bit&7u)); }
static void progress_set_cell_bit(uint8_t cell, uint8_t bit) {
    uint16_t a=(uint16_t)(0xC100u+cell);
    W8(a,(uint8_t)(R8(a)|progress_mask(bit)));
}

static void transition_consume_resource(void) { /* $5C56 */
    if (R8(0xC0EF)==0) W8(0xC0DE,(uint8_t)(R8(0xC0DE)-1u));
}
static void patch_gate_bit5(void) { W8(0xDC17,0); W8(0xDC18,0); }
static void patch_gate_bit6(void) { W8(0xDC31,0x18); W8(0xDC41,0); W8(0xDC51,0x19); }
static void patch_gate_bit7(void) { W8(0xDC3E,0x22); W8(0xDC4E,0); W8(0xDC5E,0x23); }

bool gaw_world_pre_callback_transition(void) {
    if (R8(0xC0BA)==0) return false;
    if (R8(0xC0EF)==0 && R8(0xC0DE)==0) return false;
    GawEntity *p=gaw_entity(0);
    uint8_t held=R8(RAM_INPUT_HELD), dir=p->raw[ENT_DIRECTION];
    uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID);

    if (dir==1) return false;
    if (dir==0) {
        if ((held&0x01u)==0 || p->raw[0x11]!=0x28u || !descriptor_is_a0(p,0,-16) || R8(0xDC18)==0) return false;
        transition_consume_resource();
        progress_set_cell_bit(cell,5);
        patch_gate_bit5();
    } else if (dir==2) {
        if ((held&0x04u)==0 || p->raw[0x13]!=0x20u || !descriptor_is_a0(p,-16,-8) || R8(0xDC41)==0) return false;
        transition_consume_resource();
        progress_set_cell_bit(cell,6);
        progress_set_cell_bit((uint8_t)((cell&0xF0u)|((cell-1u)&0x0Fu)),7);
        patch_gate_bit6();
    } else {
        if ((held&0x08u)==0 || p->raw[0x13]!=0xE0u || !descriptor_is_a0(p,8,-8) || R8(0xDC4E)==0) return false;
        transition_consume_resource();
        progress_set_cell_bit(cell,7);
        progress_set_cell_bit((uint8_t)((cell&0xF0u)|((cell+1u)&0x0Fu)),6);
        patch_gate_bit7();
    }
    W8(0xDE08,0xA5);
    gaw_world_finalize_transition();
    return true;
}

void gaw_world_reload_after_scroll(void) {
    W8(0xC0AD,0); W8(0xC0AC,0);
    gaw_assets_update_interior_palette();
    if (R8(0xC072)!=0) gaw_wait_frame();
    if (gaw_world_load_current_cell()) gaw_world_expand_metatiles();
}

/* $18E9 + gameplay-visible portion of $21A1. */
static void world_prepare_boundary_crossing(void) {
    uint8_t mask=0;
    for (unsigned i=0;i<8;++i) mask=(uint8_t)((mask<<1)|(gaw_ram_read8((uint16_t)(0xC600u+i*0x30u))!=0));
    W8((uint16_t)(0xC200u+(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID)),mask);
    W8(RAM_MAIN_STATE,0x0A);
    gaw_ram_write16le(0xC314,0); gaw_ram_write16le(0xC316,0);
    W8(0xC304,0);
    for (unsigned i=1;i<32;++i) W8((uint16_t)(0xC303u+i*0x30u),0);
    W8(0xC303,R8(0xC303)|1u);gaw_render_build_sms_sat();
}

/* $21C5/$21CB: the five exits from $77 form a route puzzle. Only $76 and
   the final successful $67 exit change the cell; other attempts scroll back
   into $77 while advancing or resetting the route counter. */
void gaw_world_change_neighbor(uint8_t delta, bool wrap_nibble) {
    uint16_t id=gaw_ram_read16le(RAM_WORLD_CELL_ID);
    uint8_t old=(uint8_t)id;
    uint8_t next=(uint8_t)(old+delta);
    if (wrap_nibble) next=(uint8_t)((old&0xF0u)|(next&0x0Fu));
    if(R8(0xC040)!=0||old!=0x77u||next==0x76u){W8(0xC0B9,next);W8(0xC06C,0);return;}
    uint8_t stage=(uint8_t)(R8(0xC06C)+1u);W8(0xC06C,stage);
    if((stage==1u&&next==0x78u&&R8(0xC311)>=0x60u)||
       (stage==2u&&next==0x67u)||
       (stage==3u&&next==0x78u&&R8(0xC311)<0x60u)||
       (stage==4u&&next==0x87u))return;
    if(stage==5u&&next==0x67u){
        uint8_t mask=0;
        for(unsigned i=0;i<8u;++i)mask=(uint8_t)((mask<<1)|(R8(0xC600u+i*0x30u)!=0));
        W8(0xC277u,mask);W8(0xC0B9,next);return;
    }
    W8(0xC06C,0);
}

static void world_swap_scroll_buffers(void){
    for(unsigned i=0;i<0x500u;++i){uint8_t byte=R8(0xD100u+i);W8(0xD100u+i,R8(0xD600u+i));W8(0xD600u+i,byte);}
}
static void world_frozen_frame(void){W8(0xC033,1);gaw_wait_frame();W8(0xC033,0);}
static void world_video_address(uint16_t a){gaw_sms_vdp_control_write((uint8_t)a);gaw_sms_vdp_control_write((uint8_t)(a>>8));}
static void world_scroll_rows(uint16_t source){
    world_frozen_frame();world_video_address(0x7800u);
    for(unsigned i=0;i<0x500u;++i)gaw_sms_vdp_data_write(R8((uint16_t)(source+i)));
}
static void world_scroll_column(uint16_t column,uint8_t scroll){
    W8(0xC018,(uint8_t)((scroll&0x3Eu)<<2));world_frozen_frame();
    for(unsigned row=0;row<20u;++row){
        uint16_t destination=(uint16_t)(column+row*64u),source=(uint16_t)(destination+0x5E00u);
        world_video_address(destination);gaw_sms_vdp_data_write(R8(source));gaw_sms_vdp_data_write(R8((uint16_t)(source+1u)));
    }
}
static void world_scroll_line(bool enabled){
    if(enabled){W8(0xC01A,0x9F);gaw_ram_write16le(0xC02C,0x0275);W8(0xC010,R8(0xC010)|0x10u);}
    else{W8(0xC018,0);gaw_ram_write16le(0xC02C,0x0263);W8(0xC010,R8(0xC010)&~0x10u);}
    world_video_address((uint16_t)(0x8000u|R8(0xC010)));
}

bool gaw_world_check_boundary_transition(void) {
    GawEntity *p=gaw_entity(0);
    uint8_t y=p->raw[0x13], x=p->raw[0x11];
    uint8_t delta=0; bool wrap=false;
    if (y<0x10u) { delta=0xFFu; wrap=true; gaw_entity_set16(p,ENT_ACCUM1,0x1000); }
    else if (y>=0xF1u) { delta=0x01u; wrap=true; gaw_entity_set16(p,ENT_ACCUM1,0xF000); }
    else if (x<0x10u) { delta=0xF0u; gaw_entity_set16(p,ENT_ACCUM0,0x1000); }
    else if (x>=0xA1u) { delta=0x10u; gaw_entity_set16(p,ENT_ACCUM0,0xA000); }
    else return false;

    world_prepare_boundary_crossing();
    world_swap_scroll_buffers();gaw_world_change_neighbor(delta,wrap);
    gaw_world_reload_after_scroll();
    if(wrap){
        bool left=y<0x10u;world_scroll_line(true);
        for(unsigned remaining=32u;remaining;--remaining){
            if(remaining>=5u)for(unsigned i=0;i<16u;++i)W8(0xDD80u+i*2u,R8(0xDD80u+i*2u)+(left?8u:0xF8u));
            uint8_t offset=(uint8_t)((left?remaining-1u:32u-remaining)*2u);
            world_scroll_column((uint16_t)(0x7800u+offset),(uint8_t)(left?-offset:~offset));
        }
        gaw_entity_set16(p,ENT_ACCUM1,left?0xF000u:0x1000u);world_scroll_line(false);
    }else{
        bool up=x<0x10u;if(up)world_swap_scroll_buffers();
        uint16_t source=up?0xD5C0u:0xD140u;
        for(unsigned remaining=20u;remaining;--remaining){
            if(remaining>=3u){
                for(uint16_t sprite=0xDD40u;R8(sprite)!=0xD0u;++sprite)W8(sprite,R8(sprite)+(up?8u:0xF8u));
            }
            world_scroll_rows(source);source=(uint16_t)(source+(up?0xFFC0u:0x40u));
        }
        gaw_entity_set16(p,ENT_ACCUM0,up?0xA000u:0x1000u);
        if(up)world_swap_scroll_buffers();
    }
    return true;
}


/* $30E8: save local slots, wipe the old screen and prepare Arthur's entry. */
void gaw_world_teleport(uint16_t target_cell) {
    uint8_t mask=0;
    for (unsigned i=0;i<8;++i) mask=(uint8_t)((mask<<1)|(R8((uint16_t)(0xC600u+i*0x30u))!=0));
    W8((uint16_t)(0xC200u+(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID)),mask);
    gaw_ram_write16le(RAM_WORLD_CELL_ID,target_cell);
    gaw_ui_wipe_name_table();
    memset(gaw_ram_ptr(0xC330),0,0x5D0u);
    (void)gaw_world_load_current_cell();
    W8(RAM_MAIN_STATE,0x08); W8(0xC0E9,0);
    W8(0xC0DF,0);gaw_assets_update_inventory();
    W8(0xC30A,1);
    gaw_ram_write16le(0xC310,0x7000); gaw_ram_write16le(0xC312,0x8800);
}
