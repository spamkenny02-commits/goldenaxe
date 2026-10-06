#include "include/gaw_assets.h"
#include "include/gaw_video.h"
#include "include/gaw_ram.h"

static void address(uint16_t a){gaw_sms_vdp_control_write((uint8_t)a);gaw_sms_vdp_control_write((uint8_t)(a>>8));}
static uint8_t rom(uint8_t bank,uint16_t a){return gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
uint16_t gaw_assets_unpack_tiles(uint8_t bank,uint16_t source,uint16_t destination){
    for(unsigned plane=0;plane<4u;++plane){
        uint16_t dst=(uint16_t)(destination+plane);
        for(;;){
            uint8_t command=rom(bank,source++);if(command==0)break;
            unsigned count=command&0x7Fu;if(count==0)count=256u;
            uint8_t value=0;if(!(command&0x80u))value=rom(bank,source++);
            while(count--){
                if(command&0x80u)value=rom(bank,source++);
                address(dst);
                gaw_sms_vdp_data_write(value);dst=(uint16_t)(dst+4u);
            }
        }
        gaw_ram_write16le(0xC031u,dst);
    }
    return source;
}
static uint16_t copy_vram(uint16_t source,uint16_t destination){
    for(unsigned i=0;i<32u;++i){
        address((uint16_t)(source&0x3FFFu));
        uint8_t value=gaw_sms_vdp_data_read();
        address(destination++);gaw_sms_vdp_data_write(value);++source;
    }
    return source;
}
static void clear_vram(uint16_t destination){address(destination);for(unsigned i=0;i<32u;++i)gaw_sms_vdp_data_write(0);}
void gaw_assets_load_item(uint8_t item,uint16_t destination){
    if(item<0x1Eu){
        uint16_t source=(uint16_t)(0xA801u+(uint16_t)item*0x80u);
        address(destination);
        for(unsigned i=0;i<0x80u;++i)gaw_sms_vdp_data_write(rom(4,(uint16_t)(source+i)));
    }else if(item==0x1Eu){
        uint16_t source=copy_vram(0x32C0u,destination);
        clear_vram((uint16_t)(destination+32u));
        (void)copy_vram(source,(uint16_t)(destination+64u));
        clear_vram((uint16_t)(destination+96u));
    }else if(item>=0x21u&&item<0x2Au){
        (void)copy_vram((uint16_t)(0x3040u+(item-0x21u)*32u),destination);
    }else if(item==0x2Au){
        (void)gaw_assets_unpack_tiles(4,0xBBB9u,destination);
    }
}
