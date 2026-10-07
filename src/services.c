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
static uint16_t page(void){return R(0xDFFCu)&4u?0x4000u:0u;}
static uint8_t saved(uint16_t a){return gaw_platform_sram_read((uint16_t)(page()+(a&0x3FFFu)));}
static void save_byte(uint16_t a,uint8_t v){gaw_platform_sram_write((uint16_t)(page()+(a&0x3FFFu)),v);}
static void sram_enable(void){W(0xDFFCu,R(0xDFFCu)|8u);}
static void sram_disable(void){W(0xDFFCu,R(0xDFFCu)&0xF7u);}
static void message_wait(uint16_t source){gaw_menu_message(source);gaw_menu_wait_input(0x3F);}
static void pay_steps(uint8_t cost){unsigned n=cost?cost:256u;while(n--){W(0xC0DDu,R(0xC0DDu)-1u);gaw_hud_animate_value(3);}}
static int pay(uint8_t cost){
    if(!cost)return 1;
    if(R(0xC0DDu)<cost){gaw_menu_message(0x8BCDu);return 0;}
    gaw_menu_message(0x8BC2u);pay_steps(cost);return 1;
}
static void heal(void){while(R(0xC318u)!=R(0xC0DAu)){W(0xC318u,R(0xC318u)+1u);gaw_hud_animate_value(1);}}
void gaw_menu_cursor(void){
    uint8_t old=R(0xC0A0u),selected=old,pressed=R(RAM_INPUT_PRESSED);
    if((pressed&1u)&&selected)--selected;
    if((pressed&2u)&&selected!=R(0xC0A1u))++selected;
    if(selected!=old){W(0xC0A0u,selected);W(0xDE08u,0x95);}
    if(pressed&0x20u)W(0xDE08u,0xAB);
    W(0xD111u,selected*24u+8u);W(0xD113u,0x68);gaw_ui_sprite(1,0x7383u,0xD100u);
}
uint8_t gaw_menu_choose(uint8_t limit){
    W(0xC0A1u,limit);gaw_wait_frame();gaw_ui_upload_name_table();
    for(;;){
        gaw_wait_frame();W16(0xC024u,0xDD40);W16(0xC026u,0xDD80);gaw_menu_cursor();W(R16(0xC024u),0xD0);
        if(R(RAM_INPUT_PRESSED)&0x20u)break;
        if(R(RAM_INPUT_PRESSED)&0x10u){W16(0xC0A0u,(uint16_t)(limit|((uint16_t)limit<<8)));break;}
    }
    return R(0xC0A0u);
}
void gaw_services_draw_portrait(void){
    uint16_t source=word(7,(uint16_t)(0xAB2Bu+(uint8_t)(R(0xC0A7u)*2u)));
    source=gaw_assets_unpack_tiles(7,source,0x4000u);(void)gaw_assets_unpack_descriptors(7,source,0xD200u);
    gaw_ui_box(0xD644u,10,10);
    for(unsigned y=0;y<8u;++y)for(unsigned x=0;x<16u;++x)W(0xD686u+y*64u+x,R(0xD200u+y*16u+x));
    for(unsigned i=0;i<512u;++i){address((uint16_t)(0x4002u+i*4u));gaw_sms_vdp_data_write(0xFF);}
    gaw_wait_frame();gaw_ui_upload_name_table();
    for(uint8_t mask=0x7F;;mask>>=1){
        uint8_t value=mask;
        for(unsigned i=0;i<512u;++i){address((uint16_t)(0x4002u+i*4u));gaw_sms_vdp_data_write(value);value=(uint8_t)((value>>2)|(value<<6));}
        gaw_wait_frame();if(!mask)break;
    }
}
void gaw_services_draw_saves(void){
    for(unsigned i=0;i<3u;++i)(void)gaw_ui_icon_tiles(0x08A4u,(uint16_t)(0xD65Au+i*0xC0u),1);
    gaw_services_draw_save_names();
}
void gaw_services_draw_save_names(void){
    (void)gaw_ui_icon_tiles(0x08A0u,0xD89Au,1);
    uint16_t source=0x789Fu;
    for(unsigned i=0;i<3u;++i)source=gaw_ui_inventory_text_next(source,(uint16_t)(0xD660u+i*0xC0u));
    for(unsigned i=0;i<3u;++i){
        sram_enable();uint16_t slot=word(1,(uint16_t)(0x78C2u+i*2u));unsigned remaining=8;
        for(unsigned n=0;n<8u;++n){if(!saved((uint16_t)(slot+n)))break;--remaining;}
        unsigned at=0;while(remaining--)W(0xD100u+at++,0x20);
        for(unsigned n=0;n<8u;++n)W(0xD100u+at++,saved((uint16_t)(slot+n)));
        W(0xD100u+at,0);sram_disable();gaw_ui_inventory_text(0xD100u,word(1,(uint16_t)(0x78C8u+i*2u)));
    }
}
static uint16_t merchandise(uint8_t index){
    uint16_t p=0x796Au;uint8_t type;
    do{uint8_t cell=rom(1,p++);type=rom(1,p++);if(cell==R(0xC0BBu))break;}while(p<0x7986u);
    return word(1,(uint16_t)(0x7986u+(uint8_t)(type*14u)+(uint8_t)(index*2u)));
}
void gaw_services_draw_shop(void){
    gaw_menu_message(merchandise(6));
    for(unsigned i=0;i<3u;++i)(void)gaw_ui_icon_tiles((uint16_t)(0x0890u+i*4u),(uint16_t)(0xD65Au+i*0xC0u),1);
    (void)gaw_ui_icon_tiles(0x08A0u,0xD89Au,1);
    for(unsigned i=0;i<3u;++i){
        uint16_t destination=(uint16_t)(0xD660u+i*0xC0u),item=merchandise((uint8_t)(i*2u+1u));
        gaw_ui_inventory_text(merchandise((uint8_t)(i*2u)),destination);gaw_ui_decimal((uint8_t)(item>>8),(uint16_t)(destination+0x54u));
        gaw_ui_inventory_text(0x78C0u,(uint16_t)(destination+0x5Au));gaw_assets_load_item((uint8_t)item,(uint16_t)(0x5200u+i*0x80u));
    }
}
static void save_game(void){
    gaw_services_draw_portrait();gaw_services_draw_saves();gaw_menu_message(0x8D70u);
    if(gaw_ui_yes_no_fixed()!=0xFFu){message_wait(0x8DB6u);return;}
    gaw_menu_message(0x8DA7u);uint8_t slot=R(0xC036u);if(slot)--slot;W(0xC0A0u,slot);
    slot=gaw_menu_choose(3);if(slot==R(0xC0A1u))return;
    W(0xC036u,slot+1u);W(0xC0D9u,R(0xC318u));W16(0xC0C2u,R16(0xC0BBu));
    sram_enable();uint16_t destination=word(1,(uint16_t)(0x78C2u+(uint8_t)(slot*2u)));
    for(unsigned i=0;i<0x250u;++i)save_byte((uint16_t)(destination+i),R(0xC0B0u+i));
    save_byte(0x8030u,R(0xC036u));sram_disable();gaw_services_draw_saves();message_wait(0x8DDDu);
}
static uint8_t pass_price(void){
    unsigned i=0;while(i<5u&&rom(1,(uint16_t)(0x752Eu+i))!=R(0xC0BBu))++i;
    return rom(1,(uint16_t)(0x7533u+(i<5u?i:4u)));
}
static void draw_pass(void){
    gaw_menu_message(0x8FE3u);(void)gaw_ui_icon_tiles(0x0890u,0xD65Au,1);(void)gaw_ui_icon_tiles(0x08A0u,0xD71Au,1);
    gaw_ui_inventory_text(0xBED5u,0xD660u);gaw_ui_decimal(pass_price(),0xD6B4u);gaw_ui_inventory_text(0x78C0u,0xD6BAu);gaw_assets_load_item(12,0x5200u);
}
static void draw_magic(void){
    gaw_menu_message(0x8FFDu);gaw_assets_load_item(28,0x5200u);
    for(unsigned i=0;i<3u;++i){
        uint16_t dst=(uint16_t)(0xD65Au+i*0xC0u);(void)gaw_ui_icon_tiles(0x0890u,dst,1);
        unsigned amount=rom(1,(uint16_t)(0x75ACu+i));for(unsigned k=0;k<amount;++k)W16(dst+6u+k*2u,0x1990);
        gaw_ui_decimal(rom(1,(uint16_t)(0x75AFu+i)),(uint16_t)(0xD6B4u+i*0xC0u));gaw_ui_inventory_text(0x78C0u,(uint16_t)(0xD6BAu+i*0xC0u));
    }
    (void)gaw_ui_icon_tiles(0x08A0u,0xD89Au,1);
}
static void buy_item(uint8_t item,uint8_t price){
    uint16_t flag=0;
    if(item==0x19u){if(R(0xC0F2u)==2u){gaw_menu_message(0x8BEAu);return;}if(R(0xC0F2u)>2u){gaw_menu_message(0x8C01u);return;}if(pay(price))W(0xC0F2u,2);return;}
    if(item==0x1Bu){if(R(0xC318u)==R(0xC0DAu)){gaw_menu_message(0x8C45u);return;}if(pay(price))heal();return;}
    if(item==6u)flag=0xC0E2;
    else if(item==13u)flag=0xC0E9;
    else if(item==12u)flag=0xC0E8;
    else if(item==0x1Eu){if(R(0xC0DEu)>=99u){gaw_menu_message(0x8C45u);return;}if(pay(price))W(0xC0DEu,R(0xC0DEu)+1u);return;}
    if(!flag)return;
    if(R(flag)){gaw_menu_message(0x8BEAu);return;}if(pay(price))W(flag,1);
}
static void shop(void){
    gaw_services_draw_portrait();unsigned potion_shop=0;
    while(potion_shop<5u&&rom(1,(uint16_t)(0x752Eu+potion_shop))!=R(0xC0BBu))++potion_shop;
    if(potion_shop<5u){
        draw_pass();W(0xC0A0u,0);
        while(gaw_menu_choose(1)!=R(0xC0A1u)){if(R(0xC0E8u)){gaw_menu_message(0x8BEAu);continue;}if(pay(pass_price())){W(0xC0E8u,1);return;}}
        return;
    }
    unsigned i=0;while(i<4u&&rom(1,(uint16_t)(0x75A8u+i))!=R(0xC0BBu))++i;
    if(i<4u){
        draw_magic();W(0xC0A0u,0);
        for(;;){uint8_t choice=gaw_menu_choose(3);if(choice==R(0xC0A1u))return;
            if(R(0xC0DBu)==R(0xC0DCu)){gaw_menu_message(0x8C45u);gaw_menu_wait_input(0x30);return;}
            if(!pay(rom(1,(uint16_t)(0x75AFu+choice))))continue;
            unsigned amount=R(0xC0DBu)+(uint8_t)(rom(1,(uint16_t)(0x75ACu+R(0xC0A0u)))*8u);
            if(amount>255u)amount=255u;
            if(amount>=R(0xC0DCu))amount=R(0xC0DCu);
            W(0xC0DBu,amount);gaw_hud_rebuild_full();
        }
    }
    gaw_services_draw_shop();W(0xC0A0u,0);
    for(;;){uint8_t choice=gaw_menu_choose(3);if(choice==R(0xC0A1u))return;uint16_t item=merchandise((uint8_t)(choice*2u+1u));buy_item((uint8_t)item,(uint8_t)(item>>8));}
}
static void inn(void){
    gaw_services_draw_portrait();uint16_t p=0x7700u;uint8_t cost;
    do{uint8_t cell=rom(1,p++);cost=rom(1,p++);if(cell==R(0xC0BBu))break;}while(p<0x7716u);
    W16(0xDCE0u,0xDCE4);W16(0xDCE4u,cost);gaw_menu_message(cost?0x8C7Bu:0x8D3Fu);
    if(gaw_ui_yes_no_fixed()!=0xFFu){message_wait(0x8CC7u);return;}
    if(!pay(R(0xDCE4u))){gaw_menu_wait_input(0x3F);message_wait(0x8CC7u);return;}
    memcpy(gaw_ram_ptr(0xD100u),gaw_ram_ptr(0xDCA0u),32);gaw_ui_fade_out();for(unsigned i=0;i<60u;++i)gaw_wait_frame();
    W(0xC318u,R(0xC0DAu));gaw_hud_rebuild_full();memcpy(gaw_ram_ptr(0xDCA0u),gaw_ram_ptr(0xD100u),32);
    uint16_t blank=R16(0xD940u);for(unsigned i=0;i<0x1C0u;i+=2u)W16(0xD940u+i,blank);
    gaw_wait_frame();gaw_ui_upload_name_table();gaw_ui_fade_in();message_wait(0x8CF5u);
}
static void restore_magic_and_message(uint16_t source){W(0xC0DBu,R(0xC0DCu));message_wait(source);}
static void award(uint16_t source,uint16_t flag){
    uint8_t previous=R(flag);W(flag,previous+1u);
    if(!previous){uint8_t cap=(uint8_t)(R(0xC0DCu)+24u);if(cap<0x80u)W(0xC0DCu,cap);}
    restore_magic_and_message(source);
}
static void upgrade(void){
    unsigned which=0;while(which<4u&&rom(1,(uint16_t)(0x79FDu+which))!=R(0xC0BBu))++which;
    W(0xC0A7u,R(0xC0A7u)+which);gaw_services_draw_portrait();
    if(which==0u){
        uint8_t level=R(0xC0E4u);
        if(!level){if(!R(0xC0F3u)){W(0xC0F3u,1);message_wait(0xAD89u);}else if(!R(0xC0E8u))message_wait(0xADDAu);else{W(0xC0E8u,0);award(0xAE39u,0xC0E4u);}return;}
        if(level==1u){if(R(0xC0DAu)<72u)restore_magic_and_message(0xAF95u);else award(0xAFD6u,0xC0E4u);return;}
        restore_magic_and_message(0xB04Au);return;
    }
    if(which==1u){
        uint8_t level=R(0xC0E5u);
        if(level>=2u){restore_magic_and_message(0xB333u);return;}
        if(level&&R(0xC0DAu)<72u){restore_magic_and_message(0xB225u);return;}
        if(!level){uint16_t source=R(0xC0F4u)?0xB165u:0xB06Fu;W(0xC0F4u,1);gaw_menu_message(source);}else gaw_menu_message(0xB233u);
        if(gaw_ui_yes_no_fixed()!=0xFFu){message_wait(0xB3A0u);return;}
        uint8_t cost=level?100u:50u;if(R(0xC0DDu)<cost){message_wait(0x8BCDu);return;}
        pay_steps(cost);award(level?0xB3E5u:0xB35Du,0xC0E5u);return;
    }
    if(which==2u){
        uint8_t level=R(0xC0E6u);
        if(!level){if(R(0xC0DAu)<72u)message_wait(0xB431u);else award(0xB457u,0xC0E6u);return;}
        if(level>=2u){restore_magic_and_message(0xB747u);return;}
        for(unsigned i=0;i<9u;++i)if(!(R(0xC0CFu+i)&0x80u)){restore_magic_and_message(0xB5EBu);return;}
        W(0xC0F5u,1);award(0xB621u,0xC0E6u);return;
    }
    if(R(0xC0E7u))restore_magic_and_message(0xB8CAu);else award(0xB77Eu,0xC0E7u);
}
void gaw_state_services(void){
    gaw_ui_clear_playfield();for(unsigned i=0;i<8u;++i)W(0xDCA0u+i,rom(1,(uint16_t)(0x73D5u+i)));gaw_wait_frame();
    for(unsigned i=0;i<4u;++i)W16(0xDCE0u+i*2u,0xC0B0);
    gaw_ui_load_inventory_font();(void)gaw_assets_unpack_tiles(4,0xA4FCu,0x5400u);
    switch(R(0xC0A7u)){case 0:save_game();break;case 1:shop();break;case 2:inn();break;case 3:upgrade();break;default:break;}
    gaw_ui_clear_playfield();gaw_assets_restore_scene();gaw_world_rebuild_display_native();W(RAM_MAIN_STATE,0x0C);
}
