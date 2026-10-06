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
static void address(uint16_t a){gaw_sms_vdp_control_write((uint8_t)a);gaw_sms_vdp_control_write((uint8_t)(a>>8));}
static void tick(void){gaw_world_palette_cycle();gaw_wait_frame();}
static void delay(unsigned frames){while(frames--)tick();}
static void render(void){W(0xC303u,R(0xC303u)|1u);gaw_render_build_sms_sat();}
static uint8_t sine_hi(uint8_t phase){int16_t sine=(int16_t)((int8_t)rom(2,(uint16_t)(0x8000u+phase)))*2;return (uint8_t)((uint16_t)(sine*40)>>8);}
static void credit_line(void){
    for(unsigned i=0;i<64u;i+=2u)W16(0xD100u+i,0x08FF);
    uint8_t remaining=(uint8_t)(R(0xDCC0u)-1u);
    if(remaining&0x80u){
        uint16_t source=R16(0xDCC6u),dst=0xD102u;
        for(;;){
            uint8_t ch=R(source++);
            if(!ch){W(0xDCC1u,1);ch=1;}
            else if(!(ch&0x80u)){
                uint16_t p=word(3,0x8AE4u),count=word(3,0x8AE6u);
                do{uint8_t found=rom(3,p--);--count;if(found==ch)break;}while(count);
                W(dst,(uint8_t)(count+rom(3,0x8AE8u)));dst=(uint16_t)(dst+2u);continue;
            }
            remaining=(uint8_t)(0u-ch);W16(0xDCC6u,source);break;
        }
    }
    W(0xDCC0u,remaining);uint16_t destination=R16(0xDCC4u);address(destination);
    for(unsigned i=0;i<64u;++i)gaw_sms_vdp_data_write(R(0xD100u+i));
    destination=(uint16_t)(destination+64u);if((destination>>8)>=0x7Fu)destination=(uint16_t)(0x7800u|(destination&0xFFu));W16(0xDCC4u,destination);
}
void gaw_state_ending(void){
    W(0xC305u,0);
    for(;;){gaw_state_gameplay();uint8_t active=0;for(unsigned i=1;i<32u;++i)active|=R(0xC300u+i*0x30u);if(!active)break;}
    W(0xC0AEu,0);delay(216);W(0xC301u,0);
    for(;;){tick();uint8_t pos=R(0xC311u);if(pos==0x50u)break;W(RAM_INPUT_HELD,pos<0x50u?2:1);gaw_state_gameplay_update();}
    for(;;){tick();uint8_t pos=R(0xC313u);if(pos==0x80u)break;W(RAM_INPUT_HELD,pos<0x80u?8:4);gaw_state_gameplay_update();}
    gaw_world_set_audio(0x8D);gaw_assets_load_item(5,0x7780u);W16(0xC308u,0x8495);W(0xC30Bu,1);W16(0xC043u,0xA241);W(0xC042u,4);render();
    memset(gaw_ram_ptr(0xC600u),0,0x1B0u);
    for(unsigned i=0;i<9u;++i){
        uint16_t entity=(uint16_t)(0xC600u+i*0x30u);uint8_t angle=(uint8_t)(0x80u+i*16u);
        W(entity,6);W(entity+2u,rom(0,(uint16_t)(0x1EDCu+i*2u)));W16(entity+8u,0x2ACD);
        W(entity+0x13u,R(0xC313u)+sine_hi((uint8_t)(angle+64u)));W(entity+0x11u,R(0xC311u)+sine_hi(angle));
    }
    for(unsigned i=0;i<9u;++i){delay(4);W(0xC603u+i*0x30u,1);render();tick();}
    delay(240);delay(120);gaw_world_set_audio(0x88);
    for(unsigned i=0;i<11u;++i){W(0xDC00u+rom(1,(uint16_t)(0x70E7u+i)),0);for(unsigned n=0;n<30u;++n)gaw_wait_frame();}
    for(unsigned i=0;i<0x600u;i+=2u)W16(0xD600u+i,0x08FF);
    gaw_wait_frame();gaw_ui_upload_name_table();gaw_ui_load_font(32,0x5600u);W16(0xC308u,0x84E1);W(0xC30Bu,0);W(0xC302u,0xBC);render();gaw_wait_frame();
    for(unsigned i=0;i<0x500u;++i)W(0xC900u+i,rom(12,(uint16_t)(0xB34Eu+i)));
    W16(0xDCC0u,0);W16(0xDCC2u,0);W16(0xDCC4u,0x7E00);W16(0xDCC6u,0xC900);credit_line();
    do{
        uint16_t old=R16(0xDCC2u),scroll=(uint16_t)(old+48u);W16(0xDCC2u,scroll);
        uint8_t y=(uint8_t)(R(0xC019u)+(uint8_t)((scroll>>8)-(old>>8)));if(y>=0xE0u)y=0;W(0xC019u,y);
        if((scroll^old)&0x0800u)credit_line();
        gaw_wait_frame();
    }while(!R(0xDCC1u));
    gaw_menu_wait_input(0x30);W(RAM_MAIN_STATE,0);
}
