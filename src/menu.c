#include <string.h>
#include "include/gaw_assets.h"
#include "include/gaw_core.h"
#include "include/gaw_menu.h"
#include "include/gaw_ram.h"
#include "include/gaw_ui.h"
#include "include/gaw_video.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint8_t rom(uint8_t bank,uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
static uint16_t word(uint8_t bank,uint16_t a){return (uint16_t)(rom(bank,a)|((uint16_t)rom(bank,a+1u)<<8));}
void gaw_menu_message(uint16_t resource){
    for(unsigned i=0;i<0x1C0u;i+=2u)W16(0xD940u+i,0x18FF);
    gaw_ui_show_prepared_message(resource);
}
void gaw_menu_wait_input(uint8_t mask){do{gaw_wait_frame();}while(!(R(RAM_INPUT_PRESSED)&mask));}
void gaw_menu_reset_sound(void){W(0xDE0Bu,0x0C);W16(0xDE0Cu,0x0404);gaw_ui_menu_reset();}
void gaw_menu_load_name_resources(void){
    gaw_assets_load_masked(0,0x1435u,0x7000u,0x38,3);gaw_assets_load_masked(3,0x8776u,0x5400u,0x180,2);
    gaw_ui_load_font(32,0x5A00u);(void)gaw_assets_unpack_tiles(4,0xA74Cu,0x5E00u);(void)gaw_assets_unpack_tiles(4,0xA707u,0x5F40u);
}
static uint16_t name_tiles(uint16_t source,uint16_t destination,unsigned count,unsigned stride){
    for(unsigned i=0;i<count;++i){W(destination,rom(3,source++));W(destination+1u,8);destination=(uint16_t)(destination+stride);}
    return source;
}
void gaw_name_cursor(void){
    uint8_t held=R(RAM_INPUT_HELD),pressed=R(RAM_INPUT_PRESSED);uint16_t repeat=R16(0xD121u);
    if(!(held&15u))repeat=0;
    uint8_t delay=(uint8_t)(repeat>>8);++delay;repeat=(uint16_t)((uint16_t)delay<<8|(repeat&0xFFu));
    if(delay>=((repeat&0xFFu)?8u:24u)){repeat=1;pressed|=held&15u;}
    W16(0xD121u,repeat);
    uint8_t old=R(0xC0A0u),selected=old;
    if((pressed&4u)&&selected) --selected;
    else if((pressed&8u)&&selected<41u) ++selected;
    else{
        if((pressed&1u)&&selected>=12u){if(selected<40u)selected=(uint8_t)(selected-12u);else selected=selected==40u?32u:34u;}
        if((pressed&2u)&&selected<36u){
            if(selected<28u)selected=(uint8_t)(selected+12u);
            else selected=selected<31u?39u:selected<34u?40u:41u;
        }
    }
    W(0xC0A0u,selected);if(selected!=old)W(0xDE08u,0x95);
    W16(0xC024u,0xDD40);W16(0xC026u,0xDD80);
    uint16_t position=word(0,(uint16_t)(0x1398u+(uint8_t)(selected*2u)));
    W(0xD111u,position);W(0xD113u,position>>8);
    gaw_ui_sprite(0,selected<40u?0x13ECu:selected==40u?0x13F9u:0x1418u,0xD100u);
    position=word(0,(uint16_t)(0x1388u+R(0xD120u)));W(0xD111u,position);W(0xD113u,position>>8);gaw_ui_sprite(0,0x1431u,0xD100u);
    W(R16(0xC024u),0xD0);
}
void gaw_name_input(void){
    uint8_t pressed=R(RAM_INPUT_PRESSED),selected=R(0xC0A0u),offset=R(0xD120u);
    if(pressed&0x20u){
        if(selected<40u){
            (void)name_tiles((uint16_t)(0x8B48u+selected),(uint16_t)(0xD81Cu+offset),1,4);W(0xDE08u,0x96);gaw_ui_upload_name_table();
            offset=(uint8_t)(offset+2u);if(offset==16u)W(0xC0A0u,41);else W(0xD120u,offset);return;
        }
        if(selected>40u){
            for(unsigned i=0;i<8u;++i){
                uint8_t glyph=R(0xD81Cu+i*2u);unsigned index=0;while(index<40u&&rom(3,(uint16_t)(0x8B48u+index))!=glyph)++index;
                W(0xC0B0u+i,rom(3,(uint16_t)(0x8B48u+index+(index<40u?40u:39u))));
            }
            uint16_t p=0xC0B8u;uint8_t length=0;W(p,0);
            /* $123F/$124C decrement twice: preserve the reference revision's
               observable trailing-space scan, including its skipped bytes. */
            for(unsigned i=0;i<8u;++i){--p;if(R(p)==0x20u){if(!length)W(p,0);}else ++length;--p;}
            if(length)W(RAM_MAIN_STATE,4);else W(0xDE08u,0x96);
            return;
        }
    }else if(!(pressed&0x10u))return;
    offset=(uint8_t)(offset-2u);if(!(offset&0x80u))W(0xD120u,offset);
}
void gaw_state_name_entry(void){
    memset(gaw_ram_ptr(0xC0B0u),0,0x150u);gaw_ui_menu_reset();gaw_hud_initialize_status_descriptor();gaw_menu_load_name_resources();
    gaw_ui_box(0xD7CEu,17,3);gaw_ui_box(0xD904u,27,11);
    uint16_t source=gaw_ui_fixed_text_next(0x8AEAu,0xD690u);source=gaw_ui_fixed_text_next(source,0xD710u);(void)gaw_ui_fixed_text_next(source,0xD812u);
    source=name_tiles(0x8B19u,0xD988u,12,4);source=name_tiles(source,0xDA08u,12,4);source=name_tiles(source,0xDA88u,12,4);
    source=name_tiles(source,0xDB08u,4,4);source=name_tiles(source,0xDB26u,4,2);(void)name_tiles(source,0xDB30u,3,2);
    for(unsigned i=0;i<0x300u;++i)W(0xD601u+i*2u,R(0xD601u+i*2u)&0xEFu);
    gaw_ui_upload_name_table();W16(0xC0A0u,0);W16(0xD121u,0);gaw_ui_fade_in();
    do{gaw_wait_frame();gaw_name_cursor();gaw_name_input();}while(R(RAM_MAIN_STATE)==0x12u);
    gaw_menu_reset_sound();gaw_hud_initialize_status_descriptor();(void)gaw_assets_unpack_tiles(4,0xA74Cu,0x5E00u);gaw_ui_fade_in();
    W16(0xDCE0u,0xC0B0);gaw_menu_message(0xAB68u);gaw_menu_wait_input(0x3F);gaw_menu_reset_sound();
}
