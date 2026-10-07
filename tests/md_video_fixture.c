/* Standalone hardware fixture. No game ROM, assets, or game dispatcher is linked. */
#include <stdint.h>
#include "gaw_core.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_video.h"

volatile uint16_t gaw_video_fixture_ready;
static unsigned stage;

static void reg(unsigned index,uint8_t value){
    gaw_sms_vdp_control_write(value);
    gaw_sms_vdp_control_write((uint8_t)(0x80u|index));
}
static void address(uint16_t at){
    gaw_sms_vdp_control_write((uint8_t)at);
    gaw_sms_vdp_control_write((uint8_t)(0x40u|(at>>8)));
}
static unsigned pixel(unsigned tile,unsigned x,unsigned y){
    return ((tile+1u)>>(x%5u))&1u?1u+(tile+y)%3u:0u;
}
static uint16_t descriptor(unsigned row,unsigned col){
    unsigned palette=(row+col)&1u;
    if(stage&&row==7u&&col==5u)palette^=1u;
    return (uint16_t)(row|(palette<<11)|((col&2u)?0x1000u:0u)|
                      ((col&4u)?0x0200u:0u)|((col&8u)?0x0400u:0u));
}
static void palette(void){
    uint8_t colors[32]={0};
    colors[0]=(uint8_t)(stage?0x03u:0x0Cu);
    colors[1]=0x30;colors[2]=0x3C;colors[3]=0x3F;
    colors[16]=(uint8_t)(stage?0x0Cu:0x03u);
    colors[17]=0x0F;colors[18]=0x33;colors[19]=0x3C;colors[31]=0x3F;
    gaw_sms_vdp_control_write(0);gaw_sms_vdp_control_write(0xC0);
    gaw_sms_vdp_data_write_block(colors,sizeof colors);
    reg(7,(uint8_t)(stage==2u?0u:2u));
}
static void setup(void){
    reg(0,0x04);reg(1,0x40);reg(2,0x0E);reg(5,0x7E);
    reg(6,0);reg(8,0);reg(9,0);reg(10,0xFF);
    for(unsigned tile=0;tile<28u;++tile){
        uint8_t bytes[32]={0};
        for(unsigned y=0;y<8u;++y)
        for(unsigned x=0;x<8u;++x)
        for(unsigned plane=0;plane<4u;++plane)
            bytes[y*4u+plane]|=(uint8_t)(((pixel(tile,x,y)>>plane)&1u)<<(7u-x));
        address((uint16_t)(tile*32u));
        gaw_sms_vdp_data_write_block(bytes,sizeof bytes);
    }
    address(32u*32u);
    for(unsigned i=0;i<32u;++i)gaw_sms_vdp_data_write(0xFF);
    address(0x3800);
    for(unsigned row=0;row<28u;++row)
    for(unsigned col=0;col<32u;++col){
        uint16_t d=descriptor(row,col);
        gaw_sms_vdp_data_write((uint8_t)d);
        gaw_sms_vdp_data_write((uint8_t)(d>>8));
    }
    address(0x3F00);
    for(unsigned i=0;i<8u;++i)gaw_sms_vdp_data_write(49);
    gaw_sms_vdp_data_write(0xD0);
    address(0x3F80);
    for(unsigned i=0;i<8u;++i){
        gaw_sms_vdp_data_write((uint8_t)(i*8u));
        gaw_sms_vdp_data_write(32);
    }
    palette();
}

/* Only a hardware frame barrier and controller input are needed in this fixture. */
void gaw_vblank_tick(uint8_t held_bits){
    gaw_ram_write8(RAM_INPUT_HELD,held_bits);
    gaw_ram_write8(RAM_VBLANK_WAIT_FLAG,0);
}
void gaw_irq_service(uint8_t held_bits){(void)held_bits;}
void gaw_nmi_pause(void){
    gaw_ram_write8(RAM_PAUSE_NMI_COUNTER,(uint8_t)(gaw_ram_read8(RAM_PAUSE_NMI_COUNTER)+1u));
}
void md_main(void){
    gaw_video_fixture_ready=0xFFFFu;
    gaw_video_reset();gaw_platform_init();setup();
    uint8_t old=0;
    for(;;){
        gaw_ram_write8(RAM_VBLANK_WAIT_FLAG,1);
        gaw_platform_wait_vblank();
        gaw_video_fixture_ready=(uint16_t)stage;
        uint8_t held=(uint8_t)(gaw_ram_read8(RAM_INPUT_HELD)&0x10u);
        if(held&&!old){
            stage=(stage+1u)%3u;palette();
            uint16_t d=descriptor(7,5);
            address((uint16_t)(0x3800u+2u*(7u*32u+5u)));
            gaw_sms_vdp_data_write((uint8_t)d);
            gaw_sms_vdp_data_write((uint8_t)(d>>8));
        }
        old=held;
    }
}
