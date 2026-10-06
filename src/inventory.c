#include "include/gaw_assets.h"
#include "include/gaw_core.h"
#include "include/gaw_entity.h"
#include "include/gaw_player.h"
#include "include/gaw_ram.h"
#include "include/gaw_ui.h"
#include "include/gaw_video.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint8_t rom(uint8_t bank,uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
static uint16_t word(uint8_t bank,uint16_t a){return (uint16_t)(rom(bank,a)|((uint16_t)rom(bank,a+1u)<<8));}
static void address(uint16_t a){gaw_sms_vdp_control_write((uint8_t)a);gaw_sms_vdp_control_write((uint8_t)(a>>8));}

/* $BCEF/$BD6C: visited cells are clipped by the dungeon's eight row masks. */
static void dungeon_map(void){
    gaw_assets_load_masked(4,0xBDA1u,0x7E80u,8,3);
    address(0x5000u);
    for(unsigned i=0;i<0x300u;++i){gaw_sms_vdp_data_write(0xFF);gaw_sms_vdp_data_write(0);}
    uint16_t tile=0x0880u;
    for(unsigned y=0;y<6u;++y)for(unsigned x=0;x<8u;++x)W16(0xD6EAu+y*64u+x*2u,tile++);
    uint16_t record=(uint16_t)(0xBC8Cu+(uint8_t)(R(0xC037u)*9u));uint8_t base=rom(4,record++);
    for(unsigned y=0;y<8u;++y)for(unsigned x=0;x<8u;++x){
        uint8_t row=(uint8_t)(base+y*16u),cell=(uint8_t)((row&0xF0u)|((row+x)&15u));
        if(!(R(0xC100u+cell)&0x10u)||!(rom(4,record+y)&rom(0,(uint16_t)(0x0045u+x))))continue;
        for(unsigned pixel=y*6u;pixel<y*6u+5u;++pixel){
            uint16_t dst=(uint16_t)(0x5002u+((pixel&0xF8u)>>3)*256u+((pixel&7u)<<2)+(x*8u&0x38u)*4u);
            address(dst);gaw_sms_vdp_data_write(1);
        }
    }
}
/* $BC2B: blink the current cell on the overworld or dungeon map. */
static void map_marker(void){
    if(!(R(RAM_FRAME_COUNTER)&4u)||R(0xC040u)==1u)return;
    uint8_t cell=R(0xC0B9u),x,y;
    if(!R(0xC040u)){cell=(uint8_t)(cell-0x10u);y=(uint8_t)((cell&15u)*4u+0xAAu);x=(uint8_t)((cell>>4)*3u+0x1Au);}
    else{
        uint8_t base=rom(4,(uint16_t)(0xBC8Cu+(uint8_t)(R(0xC037u)*9u)));
        y=(uint8_t)(((uint8_t)(cell-base)&15u)*8u+0xA8u);
        uint8_t delta=(uint8_t)((cell&0xF0u)-(base&0xF0u));
        x=(uint8_t)((delta>>2)+(delta>>3)+0x18u);
    }
    W(0xD141u,x);W(0xD143u,y);gaw_ui_sprite(4,0xBC91u,0xD130u);
}
static void icon(uint8_t item,uint16_t destination){
    if(item)gaw_assets_load_item(item,destination);
    else{address(destination);for(unsigned i=0;i<0x80u;++i)gaw_sms_vdp_data_write(0);}
}
/* $729B: four consecutive tiles per 2x2 icon, with six-byte column stride. */
static uint16_t descriptors(uint16_t tile,uint16_t destination,unsigned count){
    for(unsigned i=0;i<count;++i){W16(destination,tile++);W16(destination+2u,tile++);W16(destination+64u,tile++);W16(destination+66u,tile++);destination=(uint16_t)(destination+6u);}
    return tile;
}
static void selection(void){
    uint8_t pressed=R(RAM_INPUT_PRESSED),old=R(0xC0A0u),selected=old,col=old&3u;
    if((pressed&4u)&&col)--selected;
    if((pressed&8u)&&col!=3u)++selected;
    uint8_t row=(selected&12u)>>2;
    if((pressed&1u)&&row)selected=(uint8_t)(selected-4u);
    if((pressed&2u)&&row!=2u)selected=(uint8_t)(selected+4u);
    W(0xC0A0u,selected);if(selected!=old)W(0xDE08u,0x95);
    uint16_t position=word(1,(uint16_t)(0x736Bu+(uint8_t)(selected*2u)));
    W(0xD211u,position);W(0xD213u,position>>8);gaw_ui_sprite(1,0x7383u,0xD200u);
    if(!(pressed&0x20u))return;
    if(!R(0xC0E0u+selected)||((selected==9u||selected==11u)&&R(0xC040u))){W(0xDE08u,0xA1);return;}
    W(0xC0DFu,selected);W(0xDE08u,0xAB);gaw_assets_update_inventory();
}
void gaw_state_inventory(void){
    gaw_ui_clear_playfield();gaw_ui_load_font(32,0x5600u);gaw_assets_load_masked(4,0xA4D4u,0x7E00u,40,3);
    uint16_t source=gaw_assets_unpack_tiles(5,0xB609u,0x4000u);
    (void)gaw_assets_unpack_ram(5,source,0xD640u,2);
    source=gaw_assets_unpack_tiles(5,R(0xC040u)==2u?0xBBCFu:0xB7B5u,0x4100u);
    (void)gaw_assets_unpack_ram(5,source,0xD300u,2);
    for(unsigned y=0;y<8u;++y)for(unsigned x=0;x<28u;++x)W(0xD6A4u+y*64u+x,R(0xD300u+y*28u+x));
    if(R(0xC0BAu))dungeon_map();
    icon(R(0xC0E0u),0x4600u);uint8_t shield=R(0xC0E1u);icon(shield?(uint8_t)(shield+3u):0,0x4680u);
    for(unsigned i=0;i<15u;++i)icon(R(0xC0E2u+i)?(uint8_t)(6u+i):0,(uint16_t)(0x4700u+i*128u));
    icon((uint8_t)(R(0xC0F1u)+20u),0x4E80u);icon((uint8_t)(R(0xC0F2u)+23u),0x4F00u);
    uint16_t tile=descriptors(0x0830u,0xD686u,4);tile=descriptors(tile,0xD746u,4);tile=descriptors(tile,0xD806u,4);
    tile=descriptors(tile,0xD906u,5);tile=descriptors(tile,0xDA06u,1);(void)descriptors(tile,0xDA24u,1);
    gaw_ui_inventory_text(word(3,(uint16_t)(0xBE3Cu+(uint8_t)(R(0xC0F1u)*2u))),0xDA0Cu);
    gaw_ui_inventory_text(word(3,(uint16_t)(0xBE44u+(uint8_t)(R(0xC0F2u)*2u))),0xDA2Au);
    W16(0xD92Cu,0x1996);W16(0xD96Cu,0x1997);W16(0xD96Eu,0x18DB);gaw_ui_decimal(R(0xC0DEu),0xD970u);
    gaw_wait_frame();gaw_ui_upload_name_table();W(0xC0A0u,R(0xC0DFu));
    do{
        gaw_wait_frame();gaw_hud_update_status_descriptor();W16(0xC024u,0xDD40);W16(0xC026u,0xDD80);
        selection();map_marker();W(R16(0xC024u),0xD0);
    }while(!(R(RAM_INPUT_PRESSED)&0x10u));
    gaw_ui_clear_playfield();gaw_assets_restore_scene();gaw_player_update_sprite_meta(gaw_entity(0));
    gaw_render_build_sms_sat();gaw_world_rebuild_display_native();gaw_assets_update_inventory();W(RAM_MAIN_STATE,0x0C);
}
