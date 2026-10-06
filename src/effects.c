#include "include/gaw_effects.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"

/* $6DA6: restore a four-byte half-metatile at the moving effect cursor. */
static void restore_half_metatile(void){
    uint8_t y=gaw_ram_read8(0xC09Au),x=gaw_ram_read8(0xC09Bu);
    uint8_t column=(uint8_t)((x>>2)|(x<<6));
    uint16_t address=(uint16_t)(0x7800u+((uint16_t)y<<3 & 0xFF00u)+
                              (uint8_t)((uint8_t)(y<<3)|column));
    gaw_sms_vdp_control_write((uint8_t)address);
    gaw_sms_vdp_control_write((uint8_t)(address>>8));
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
int gaw_effect_native_step(uint16_t state_address){
    uint8_t state=gaw_ram_read8(state_address);
    if(state==0)return 1;
    if(state!=3u&&state!=4u)return 0;
    restore_half_metatile();
    uint8_t y=gaw_ram_read8(0xC09Au);
    gaw_ram_write8(0xC09Au,(uint8_t)(state==3u?y-8u:y+8u));
    uint8_t remaining=(uint8_t)(gaw_ram_read8((uint16_t)(state_address+1u))-1u);
    gaw_ram_write8((uint16_t)(state_address+1u),remaining);
    if(remaining==0)gaw_ram_write8(state_address,0);
    return 1;
}
