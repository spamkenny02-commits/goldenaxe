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

/* $1D0D remaps four-plane pixels through a 16-entry original lookup table.
   The scratch shifts are retained because D100-D16F is observable game RAM. */
void gaw_assets_remap_tiles(uint16_t source,uint16_t destination,uint8_t table_offset){
    for(unsigned i=0;i<16u;++i)gaw_ram_write8((uint16_t)(0xD100u+i),rom(0,(uint16_t)(0x1DA2u+table_offset+i)));
    unsigned tiles=((uint16_t)(destination-source)>>5)&0xFFu;if(!tiles)tiles=256u;
    for(unsigned tile=0;tile<tiles;++tile){
        address((uint16_t)(source&0xBFFFu));
        for(unsigned i=0;i<32u;++i)gaw_ram_write8((uint16_t)(0xD110u+i),gaw_sms_vdp_data_read());
        address((uint16_t)(source|0x4000u));
        for(unsigned row=0;row<8u;++row){
            uint16_t last=(uint16_t)(0xD113u+row*4u);
            for(unsigned pixel=0;pixel<8u;++pixel){
                uint8_t index=0;
                for(unsigned plane=0;plane<4u;++plane){
                    uint16_t p=(uint16_t)(last-plane);uint8_t v=gaw_ram_read8(p);
                    index=(uint8_t)((index<<1)|(v>>7));gaw_ram_write8(p,(uint8_t)(v<<1));
                }
                gaw_ram_write8((uint16_t)(0xD130u+row*8u+pixel),gaw_ram_read8((uint16_t)(0xD100u+index)));
            }
            for(unsigned plane=0;plane<4u;++plane){
                uint8_t value=0;
                for(unsigned pixel=0;pixel<8u;++pixel){
                    unsigned index=(plane&1u)?pixel:7u-pixel;
                    uint16_t p=(uint16_t)(0xD130u+row*8u+index);uint8_t v=gaw_ram_read8(p);
                    gaw_ram_write8(p,(uint8_t)(v>>1));
                    value=(plane&1u)?(uint8_t)((value<<1)|(v&1u)):(uint8_t)((value>>1)|((v&1u)<<7));
                }
                gaw_sms_vdp_data_write(value);
            }
        }
        source=(uint16_t)(source+32u);
    }
}
/* $722A and $7219: restore the equipped item's graphics after modal UI. */
void gaw_assets_update_inventory(void){
    uint8_t selected=gaw_ram_read8(0xC0DFu),item;
    if(selected==0)item=gaw_ram_read8(0xC0E0u);
    else if(selected==1)item=(uint8_t)(gaw_ram_read8(0xC0E1u)+3u);
    else item=(uint8_t)(selected+4u);
    gaw_assets_load_item(item,0x5D80u);
    gaw_assets_remap_tiles(0x5D80u,0x5E00u,0x30u);
    (void)gaw_assets_unpack_tiles(4,0xA2D2u,0x7600u);
}
void gaw_assets_restore_inventory(void){
    (void)gaw_assets_unpack_tiles(4,0xBDB0u,0x5A00u);
    gaw_assets_update_inventory();
}
