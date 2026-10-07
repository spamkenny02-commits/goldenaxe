#include <string.h>
#include "include/gaw_assets.h"
#include "include/gaw_core.h"
#include "include/gaw_menu.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_ui.h"
#include "include/gaw_video.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint8_t rom(uint8_t bank,uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
static uint16_t word(uint8_t bank,uint16_t a){return (uint16_t)(rom(bank,a)|((uint16_t)rom(bank,a+1u)<<8));}
static void address(uint16_t a){gaw_platform_video_command(a);}
static void upload(uint16_t source,uint16_t destination,unsigned bytes){address(destination);while(bytes--)gaw_sms_vdp_data_write(R(source++));}
static void fill(uint16_t destination,uint16_t value,unsigned bytes){for(unsigned i=0;i<bytes;i+=2u)W16(destination+i,value);}
static void sat_begin(void){W16(0xC024u,0xDD40);W16(0xC026u,0xDD80);}
static void sat_end(void){W(R16(0xC024u),0xD0);}
static void line_mode(int enabled){
    uint8_t reg=R(0xC010u);
    if(enabled){W(0xC01Au,0xBB);W16(0xC02Cu,0x0280);reg|=0x10u;}
    else{W(0xC018u,0);W16(0xC02Cu,0x0263);reg&=0xEFu;}
    W(0xC010u,reg);address((uint16_t)(0x8000u|reg));
}
static void actors_init(uint16_t source){
    W(0xDCE2u,0);memset(gaw_ram_ptr(0xC300u),0,0x300);
    for(unsigned i=0;i<16u;++i){
        uint8_t x=rom(0,source++);if(!x)break;
        uint16_t e=(uint16_t)(0xC300u+i*0x30u);W(e,1);W(e+0x11u,x);W(e+0x13u,rom(0,source++));
        W(e+0x0Eu,rom(0,source++));W(e+0x0Cu,rom(0,source++));W(e+8u,rom(0,source++));W(e+9u,rom(0,source++));
    }
}
static void actors_frame(void){
    uint8_t frame=R(RAM_FRAME_COUNTER);if(!(frame&3u))W(0xDCE2u,R(0xDCE2u)+1u);
    sat_begin();
    for(unsigned i=0;i<16u;++i){
        uint16_t e=(uint16_t)(0xC300u+i*0x30u);uint8_t state=R(e);if(!state)continue;
        if(state!=2u){if(R(0xDCE2u)!=R(e+0x0Eu))continue;W(e,state+1u);}
        uint16_t descriptor=word(0,(uint16_t)(R16(e+8u)+R(e+0x0Bu)*2u));gaw_ui_sprite(0,descriptor,e);
        if(frame&3u)continue;
        uint8_t pose=(uint8_t)(R(e+0x0Bu)+1u);W(e+0x0Bu,pose);
        if(pose==R(e+0x0Cu)){W(e,R(e)-1u);W(e+0x0Bu,0);}
    }
    sat_end();
}
static void intro_callback(void){
    uint16_t callback=R16(0xDCECu);uint8_t frame=R(RAM_FRAME_COUNTER);
    if(callback==0x0F37u){
        if(frame&7u)return;
        uint8_t phase=(uint8_t)(R(0xDCE2u)+1u);if(phase>=6u)phase=0;W(0xDCE2u,phase);
        for(unsigned i=0;i<3u;++i)W(0xDCA1u+i,rom(5,(uint16_t)(0xBE13u+phase*3u+i)));
    }else if(callback==0x104Au){
        actors_frame();uint16_t p=R(0xDD40u)==0xD0u?0xBE57u:(uint16_t)(0xBE5Du+3u*((frame>>1)&7u));
        for(unsigned i=0;i<3u;++i)W(0xDCA1u+i,rom(5,p++));
        for(unsigned i=0;i<3u;++i){uint8_t color=rom(5,p++);for(unsigned j=0;j<4u;++j)W(0xDCA4u+i*4u+j,color);}
    }else if(callback==0x1055u){W(0xDCB2u,rom(0,(uint16_t)(0x10BFu+(frame&3u))));actors_frame();}
}
/* The assembly unwinds SP at $0D0B/$16C9. C propagates the skip through
   these routines instead; C02A is obsolete CPU-stack metadata. */
static int intro_frame(void){gaw_wait_frame();intro_callback();return !(R(RAM_INPUT_PRESSED)&0x30u);}
static int intro_delay(unsigned n){while(n--)if(!intro_frame())return 0;return 1;}
static int intro_upload_top(void){if(!intro_frame())return 0;upload(0xD600u,0x7800u,0x300);return intro_frame();}
static int scene_palette(uint16_t *source){
    fill(0xD600u,0x09FA,0x300);if(!intro_upload_top())return 0;
    memset(gaw_ram_ptr(0xDCA0u),0,16);for(unsigned i=0;i<4u;++i)W(0xDCA0u+i,rom(6,(*source)++));return 1;
}
static void fill_plane3(void){for(unsigned i=0;i<0x900u;++i){address((uint16_t)(0x4003u+i*4u));gaw_sms_vdp_data_write(0xFF);}}
static int scene_reveal(void){
    for(unsigned y=0;y<12u;++y)for(unsigned x=0;x<48u;++x)W(0xD608u+y*64u+x,R(0xC900u+y*48u+x));
    if(!intro_upload_top())return 0;
    for(uint8_t mask=0x7F;;mask>>=1){
        if(!intro_frame())return 0;
        uint8_t value=mask;
        for(unsigned i=0;i<0x900u;++i){address((uint16_t)(0x4003u+i*4u));gaw_sms_vdp_data_write(value);value=(uint8_t)((value>>2)|(value<<6));}
        if(!mask)break;
    }
    return 1;
}
static int scene_image(uint16_t source,uint16_t callback){
    W16(0xDCECu,callback);if(!scene_palette(&source))return 0;
    source=gaw_assets_unpack_tiles(6,source,0x4000u);fill_plane3();(void)gaw_assets_unpack_descriptors(6,source,0xC900u);return scene_reveal();
}
static int scene_columns(void){
    uint16_t source=0xAF1Fu;if(!scene_palette(&source))return 0;
    for(unsigned plane=0;plane<2u;++plane){
        source=gaw_assets_unpack_ram(6,source,0xC900u,1);
        for(unsigned i=0;i<0x900u;++i){address((uint16_t)(0x4000u+plane+i*4u));gaw_sms_vdp_data_write(R(0xC900u+i));}
    }
    fill_plane3();uint16_t p=0xC900u;
    for(unsigned x=0;x<12u;++x)for(unsigned y=0;y<24u;++y){W16(p,x+y*12u);p=(uint16_t)(p+2u);}
    return scene_reveal();
}
static int scene_mask(void){
    (void)gaw_assets_unpack_ram(6,0xB595u,0xC900u,2);
    for(uint8_t mask=1;;mask=(uint8_t)((mask<<1)|1u)){
        uint8_t value=mask;uint16_t p=0xC900u;
        for(unsigned i=0;i<0x600u;++i){address((uint16_t)(0x4002u+i*4u));gaw_sms_vdp_data_write(R(p++)&value);gaw_sms_vdp_data_write(R(p++)&value);value=(uint8_t)((value<<2)|(value>>6));}
        if(!intro_frame())return 0;
        if(mask==0xFFu)break;
    }
    W16(0xDCECu,0x104A);actors_init(0x0FE4u);return 1;
}
static int intro_blackout(void){
    W16(0xDCECu,0x0F36);memset(gaw_ram_ptr(0xDCC0u),0,16);
    for(uint16_t p=0x0B0Eu;rom(0,p);++p)while(gaw_ui_palette_step(rom(0,p)))if(!intro_delay(4))return 0;
    return 1;
}
static void text_scroll(void){memmove(gaw_ram_ptr(0xD900u),gaw_ram_ptr(0xD940u),0x2C0);fill(0xDBC0u,0x01FA,64);}
static int text_upload(void){if(!intro_delay(2))return 0;upload(0xD900u,0x7B00u,0x300);return 1;}
static int intro_text_line(void){
    do{if(!intro_frame())return 0;}while(R(0xC030u));W(0xC030u,90);
    uint16_t source=R16(0xDCE8u);if(!rom(6,source)){W(0xDCE1u,1);return 1;}
    text_scroll();if(!text_upload())return 0;text_scroll();uint16_t destination=0xDBC2u;
    for(uint8_t glyph=rom(6,source++);glyph!=0xFFu;glyph=rom(6,source++)){W16(destination,(uint16_t)(0x0900u|glyph));destination=(uint16_t)(destination+2u);}
    W16(0xDCE8u,source);W(0xDCE0u,R(0xDCE0u)+1u);return text_upload();
}
static int intro_event(void){
    uint16_t event=R16(0xDCEAu);if(R(0xDCE0u)!=rom(0,event))return 1;
    uint16_t target=word(0,event+1u);W16(0xDCEAu,event+3u);
    if(target==0x0ED4u)return intro_blackout();
    if(target==0x0E3Fu){actors_init(0x0F95u);return scene_image(0xA655u,0x1055);}
    if(target==0x0DD2u)return scene_columns();
    if(target==0x0D8Cu)return scene_mask();
    return 1;
}
static void introduction(void){
    gaw_menu_reset_sound();(void)gaw_assets_unpack_tiles(4,0xA74Cu,0x6600u);gaw_ui_load_font(32,0x6820u);(void)gaw_assets_unpack_tiles(4,0xA7D0u,0x7400u);
    uint16_t source=0x10C3u;for(unsigned i=0;i<7u;++i)source=gaw_ui_load_choice_font_next(source);
    address(0x4000u);for(unsigned i=0;i<0x2400u;++i)gaw_sms_vdp_data_write(0);
    gaw_hud_initialize_status_descriptor();W(0xDE06u,0x85);gaw_ui_fade_in();W(0xC030u,0);W16(0xDCE0u,0);W16(0xDCEAu,0x10F1);W16(0xDCE8u,0xB9CE);W16(0xDCECu,0x0F36);
    if(!scene_image(0x9D70u,0x0F37))return;
    do{if(!intro_text_line()||!intro_event())return;}while(!R(0xDCE1u));
}
static int title_frame(void){gaw_wait_frame();return !(R(RAM_INPUT_PRESSED)&0x30u);}
static int title_delay(unsigned n){while(n--)if(!title_frame())return 0;return 1;}
static int title_animation(void){
    for(unsigned n=0;n<11u;++n)for(unsigned phase=0;phase<3u;++phase){
        if(!title_delay(6))return 0;
        for(unsigned y=0;y<9u;++y)upload((uint16_t)(0xCB00u+phase*0xEAu+y*26u),(uint16_t)(0x7CC4u+y*64u),26);
    }
    if(!title_delay(6))return 0;
    upload(0xD9C0u,0x7CC0u,0x240);
    for(unsigned i=0;i<16u;++i)W(0xDCC0u+i,rom(7,(uint16_t)(0x8000u+i)));
    for(uint16_t p=0x16BCu;rom(0,p);++p)while(gaw_ui_palette_step(rom(0,p)))if(!title_delay(6))return 0;
    if(!title_delay(60))return 0;
    for(unsigned y=0;y<8u;++y){if(!title_frame())return 0;upload((uint16_t)(0xC900u+y*64u),(uint16_t)(0x7900u+y*64u),64);}
    for(unsigned left=360u;left;--left){uint16_t row=left&0x30u?0xCDBEu:0xD840u;if(!title_frame())return 0;upload(row,0x7B40u,64);}
    return 1;
}
static uint8_t saved(uint16_t a){return gaw_platform_sram_read((uint16_t)((R(0xDFFCu)&4u?0x4000u:0u)+(a&0x3FFFu)));}
static int continue_choose(void){
    gaw_ui_menu_reset();gaw_ui_load_inventory_font();(void)gaw_assets_unpack_tiles(4,0xA4FCu,0x5400u);gaw_hud_initialize_status_descriptor();
    for(unsigned i=0;i<3u;++i)(void)gaw_ui_icon_tiles(0x08A8u,(uint16_t)(0xD65Au+i*0xC0u),1);
    gaw_services_draw_save_names();gaw_ui_fixed_text(0xBE26u,0xD9CEu);
    uint8_t slot=(uint8_t)(R(0xC036u)-1u);if(slot&0x80u)slot=3;W(0xC0A0u,slot);W(0xC0A1u,3);
    gaw_wait_frame();gaw_ui_upload_name_table();gaw_ui_fade_in();
    for(;;){
        gaw_wait_frame();sat_begin();gaw_menu_cursor();sat_end();uint8_t pressed=R(RAM_INPUT_PRESSED);
        if(pressed&0x10u)return 0;
        if(!(pressed&0x20u))continue;
        slot=R(0xC0A0u);if(slot==3u)return 0;
        uint16_t source=word(1,(uint16_t)(0x78C2u+slot*2u));W(0xDFFCu,R(0xDFFCu)|8u);uint8_t occupied=saved(source);W(0xDFFCu,R(0xDFFCu)&0xF7u);
        if(!occupied){W(0xDE08u,0xA1);continue;}
        W(0xDFFCu,R(0xDFFCu)|8u);for(unsigned i=0;i<0x250u;++i)W(0xC0B0u+i,saved((uint16_t)(source+i)));W(0xDFFCu,R(0xDFFCu)&0xF7u);
        W(0xC036u,slot+1u);W(0xC318u,R(0xC0D9u));W16(0xC0C0u,R16(0xC0C2u));W(RAM_MAIN_STATE,6);return 1;
    }
}
void gaw_title_choose(void){
    for(;;){
        gaw_ui_menu_reset();line_mode(0);gaw_world_set_audio(0x89);gaw_hud_initialize_status_descriptor();gaw_menu_load_name_resources();
        (void)gaw_assets_unpack_tiles(4,0xB701u,0x7040u);gaw_ui_box(0xD852u,14,4);gaw_ui_fixed_text(0xBE13u,0xD898u);gaw_ui_upload_name_table();gaw_ui_fade_in();W(0xC0A0u,R(0xC036u));
        for(;;){
            W16(0xD896u,R(0xC0A0u)?0x18FF:0x0982);W16(0xD8D6u,R(0xC0A0u)?0x0982:0x18FF);
            uint8_t selected=R(0xC0A0u);
            for(;;){
                gaw_ui_upload_playfield();uint8_t pressed=R(RAM_INPUT_PRESSED),next=0;
                if(pressed&1u)next=0;else if(pressed&2u)next=1;else if(pressed&0x30u)break;else continue;
                if(next==selected)continue;
                W(0xC0A0u,next);W(0xDE08u,0x95);break;
            }
            if(selected!=R(0xC0A0u))continue;
            W(0xDE08u,0xAB);
            if(!selected){W(RAM_MAIN_STATE,0x12);return;}
            if(continue_choose())return;
            break;
        }
    }
}
void gaw_state_title_intro(void){
    introduction();gaw_menu_reset_sound();
    for(unsigned i=0;i<16u;++i)W(0xDCA0u+i,rom(7,(uint16_t)(0x8000u+i)));
    uint16_t source=gaw_assets_unpack_tiles(7,0x8010u,0x4000u);source=gaw_assets_unpack_descriptors(7,source,0xD600u);(void)gaw_assets_unpack_descriptors(7,source,0xC900u);
    for(unsigned i=0;i<10u;++i)W(0xDBABu+i*2u,R(0xDBABu+i*2u)|8u);
    W(0xC019u,0x20);W(0xDCB0u,R(0xDCA0u));W(0xDCB1u,R(0xDCA1u));W(0xDCAFu,0);memset(gaw_ram_ptr(0xDCA1u),0,10);
    upload(0xD600u,0x7900u,0x600);line_mode(1);gaw_ui_fade_in();W(0xDE06u,0x81);
    if(!title_animation())gaw_title_choose();
}
