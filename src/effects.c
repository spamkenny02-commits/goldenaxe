#include "include/gaw_platform.h"
#include <string.h>
#include "include/gaw_effects.h"
#include "include/gaw_assets.h"
#include "include/gaw_core.h"
#include "include/gaw_entity.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"

/* $6DA6: restore a four-byte half-metatile at the moving effect cursor. */
static void restore_half_metatile(void){
    uint8_t y=gaw_ram_read8(0xC09Au),x=gaw_ram_read8(0xC09Bu);
    uint8_t column=(uint8_t)((x>>2)|(x<<6));
    uint16_t address=(uint16_t)(0x7800u+((uint16_t)y<<3 & 0xFF00u)+
                              (uint8_t)((uint8_t)(y<<3)|column));
    gaw_platform_video_command(address);
    uint16_t shadow=(uint16_t)(address+0x5E00u);
    uint8_t cell=(uint8_t)((y&0xF0u)|(x>>4));
    uint8_t tile=gaw_ram_read8((uint16_t)(0xDC00u+cell));
    uint16_t source=(uint16_t)(0xC900u+((uint16_t)tile<<3)+((y&8u)>>1));
    for(unsigned i=0;i<4u;++i){
        uint8_t value=gaw_ram_read8((uint16_t)(source+i));
        gaw_sms_vdp_data_write(value);
        gaw_ram_write8((uint16_t)(0xC000u+((shadow+i)&0x1FFFu)),value);
    }
}
static void full_screen_effect(unsigned kind);
int gaw_effect_native_step(uint16_t state_address){
    uint8_t state=gaw_ram_read8(state_address);
    if(state==0)return 1;
    if(state==1u||state==2u){full_screen_effect(state);return 1;}
    if(state!=3u&&state!=4u)return 0;
    restore_half_metatile();
    uint8_t y=gaw_ram_read8(0xC09Au);
    gaw_ram_write8(0xC09Au,(uint8_t)(state==3u?y-8u:y+8u));
    uint8_t remaining=(uint8_t)(gaw_ram_read8((uint16_t)(state_address+1u))-1u);
    gaw_ram_write8((uint16_t)(state_address+1u),remaining);
    if(remaining==0)gaw_ram_write8(state_address,0);
    return 1;
}

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
static uint8_t effect_rom(uint8_t bank,uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
static uint16_t effect_word(uint8_t bank,uint16_t a){return (uint16_t)(effect_rom(bank,a)|((uint16_t)effect_rom(bank,(uint16_t)(a+1u))<<8));}
static void upload_playfield(void){
    gaw_platform_video_command(0x7800u);
    /* OUTI and DJNZ each decrement B: ten groups of 128 bytes. */
    for(unsigned i=0;i<0x500u;++i)gaw_sms_vdp_data_write(R(0xD600u+i));
}
static void blank_playfield(uint8_t attributes){
    for(unsigned i=0;i<0x500u;i+=2u){W(0xD600u+i,0xFF);W(0xD601u+i,attributes);}
    W(0xC033u,1);gaw_wait_frame();W(0xC033u,0);upload_playfield();
}
static void clear_effect_sprites(void){memset(gaw_ram_ptr(0xC330),0,0x180);}
static void initialize_effect(void){
    memset(gaw_ram_ptr(0xD200),0,0x400);clear_effect_sprites();
    for(unsigned i=0;i<8u;++i){
        uint16_t e=(uint16_t)(0xC330u+i*0x30u);
        W(e,1);gaw_ram_write16le((uint16_t)(e+8u),0x6EAE);
        W(e+0x0Cu,2);W(e+0x0Du,6);W(e+0x10u,i*0x20u);
    }
    memset(gaw_ram_ptr(0xC780),0,0x180);
    for(unsigned i=0;i<16u;++i)W(0xDCA0u+i,effect_rom(15,(uint16_t)(0x8000u+i)));
}
static uint8_t scaled_sine(uint8_t phase,uint8_t radius){
    int value=(int)(int8_t)effect_rom(2,(uint16_t)(0x8000u+phase))*2*(int)radius;
    return (uint8_t)((uint16_t)value>>8);
}
static void orbit_sprites(void){
    uint8_t frame=R(0xC02Fu),radius=(uint8_t)(frame&7u);
    if(frame&8u)radius=(uint8_t)(8u-radius);
    radius=(uint8_t)(radius+16u);
    for(unsigned i=0;i<8u;++i){
        uint16_t e=(uint16_t)(0xC330u+i*0x30u);if(!R(e))continue;
        W(e+3u,R(e+3u)&0xFEu);uint8_t phase=R(e+0x10u);
        uint8_t dy=scaled_sine((uint8_t)(phase+0x40u),radius);
        int y=(int)R(0xC313u)+(int)(int8_t)dy;W(e+0x13u,y);
        if(y>=0&&y<=255&&(uint8_t)(y+4)>=8u){
            uint8_t dx=scaled_sine(phase,radius);W(e+0x11u,R(0xC311u)+dx-6u);W(e+3u,R(e+3u)|1u);
        }
        W(e+0x10u,phase+9u);W(e+2u,0xF4u+(frame&1u));
    }
    W(0xC303u,R(0xC303u)|1u);gaw_render_build_sms_sat();
}
static void finish_effect(void){
    uint8_t selected=R(0xC0DFu),level=R(0xC0E0u+selected);
    uint8_t damage=effect_rom(0,(uint16_t)(0x2D9Eu+level*5u));
    for(unsigned i=0;i<16u;++i){
        uint16_t e=(uint16_t)(0xC600u+i*0x30u);
        if(!R(e)||!R(e+0x1Bu)||!(R(e+3u)&2u))continue;
        uint8_t armor=R(e+0x1Au),amount=damage<armor?1u:(uint8_t)(damage-armor);
        W(e+0x1Du,R(e+0x1Du)+amount);gaw_ram_write16le((uint16_t)(e+0x1Eu),0xC300);
    }
    W(0xC090u,0);clear_effect_sprites();W(0xC303u,R(0xC303u)|1u);gaw_render_build_sms_sat();
    blank_playfield(8);W(0xC0DFu,0);gaw_assets_update_inventory();gaw_assets_restore_scene();gaw_world_rebuild_display_native();
}
static void fire_effect(void){
    blank_playfield(8);initialize_effect();(void)gaw_assets_unpack_tiles(5,0xA33Bu,0x4000u);
    for(unsigned i=0;i<22u;++i){uint16_t e=(uint16_t)(0xD200u+i*0x20u);W(e,22u-i);W(e+1u,0xFFu-i);gaw_ram_write16le((uint16_t)(e+2u),effect_word(1,(uint16_t)(0x6BF6u+i*2u)));}
    do{
        for(unsigned i=0;i<22u;++i){
            uint16_t e=(uint16_t)(0xD200u+i*0x20u);if(!R(e))continue;
            uint8_t phase=R(e+1u);uint16_t source=phase<14u?(uint16_t)(0xA293u+phase*12u):0x6C22u;
            uint16_t dst=gaw_ram_read16le((uint16_t)(e+2u));
            for(unsigned row=0;row<4u;++row){
                for(unsigned col=0;col<3u;++col){W(dst++,effect_rom(5,source++));if(col<2u)dst=(uint16_t)((dst&0xFF00u)|(uint8_t)(dst+1u));}
                dst=(uint16_t)(dst+0x3Bu);
            }
            W(e+1u,phase+1u);
            if(R(e+1u)==22u){W(e+1u,0);W(e+4u,R(e+4u)+1u);if(R(e+4u)==3u)W(e,0);}
        }
        if(!R(0xD360u)){clear_effect_sprites();}
        orbit_sprites();gaw_wait_frame();upload_playfield();
    }while(R(0xD4A0u));
}
static void wave_effect(void){
    initialize_effect();blank_playfield(0);(void)gaw_assets_unpack_tiles(5,0xAD48u,0x4000u);
    memcpy(gaw_ram_ptr(0xDCA0),gaw_ram_ptr(0xDCB0),16);W(0xDCA2u,0x17);
    for(unsigned i=0;i<4u;++i){uint16_t e=(uint16_t)(0xD200u+i*0x20u);W(e,4u-i);W(e+1u,i*16u);}
    do{
        for(unsigned i=0;i<4u;++i){
            uint16_t e=(uint16_t)(0xD200u+i*0x20u),record=(uint16_t)(0x6CF0u+R(e+2u)*6u);
            uint16_t dst=(uint16_t)(effect_word(1,record)+R(e+1u)),source=effect_word(1,(uint16_t)(record+2u));
            unsigned rows=effect_rom(1,(uint16_t)(record+4u)),columns=effect_rom(1,(uint16_t)(record+5u));
            for(unsigned row=0;row<rows;++row){for(unsigned b=0;b<columns*2u;++b)W(dst+b,effect_rom(5,source++));dst=(uint16_t)(dst+0x40u);}
            W(e+8u,R(e+8u)+1u);
            if(R(e+8u)==1u){W(e+8u,0);W(e+2u,R(e+2u)+1u);if(R(e+2u)>=10u){W(e+2u,7);W(e+9u,R(e+9u)+1u);}}
        }
        orbit_sprites();W(0xDCA1u,(R(0xC02Fu)&3u)?0:3);gaw_wait_frame();upload_playfield();
    }while(R(0xD209u)!=7u);
}
static void full_screen_effect(unsigned kind){if(kind==1u)fire_effect();else wave_effect();finish_effect();}
