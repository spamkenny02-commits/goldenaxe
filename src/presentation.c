#include "include/gaw_presentation.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"
#include "include/gaw_platform.h"

static uint8_t read_byte(uint8_t bank,uint16_t at,int sram){
    if(at>=0xC000u)return gaw_ram_read8((uint16_t)(0xC000u+(at&0x1FFFu)));
    if(sram&&at>=0x8000u)return gaw_platform_sram_read((uint16_t)(at-0x8000u));
    return gaw_sms_rom_bank_read(at<0x4000u?0u:at<0x8000u?1u:bank,at);
}
static void write_byte(uint16_t at,uint8_t value){if(at>=0xC000u)gaw_ram_write8((uint16_t)(0xC000u+(at&0x1FFFu)),value);}
static uint16_t read_word(uint8_t bank,uint16_t at){return (uint16_t)(read_byte(bank,at,0)|((uint16_t)read_byte(bank,(uint16_t)(at+1u),0)<<8));}
static void address(uint16_t at){gaw_sms_vdp_control_write((uint8_t)at);gaw_sms_vdp_control_write((uint8_t)(at>>8));}
static void copy(uint8_t bank,uint16_t source,unsigned count,int sram){
    while(count){
        unsigned n;
        const uint8_t *data;
        if(source>=0xC000u){
            unsigned offset=source&0x1FFFu;
            n=0x2000u-offset;data=gaw_ram_ptr((uint16_t)(0xC000u+offset));
        }else if(sram&&source>=0x8000u){
            gaw_sms_vdp_data_write(read_byte(bank,source++,1));--count;continue;
        }else{
            uint8_t selected=source<0x4000u?0u:source<0x8000u?1u:bank;
            n=0x4000u-(source&0x3FFFu);data=gaw_sms_rom_bank_data(selected,source);
        }
        if(n>count)n=count;
        gaw_sms_vdp_data_write_block(data,n);source=(uint16_t)(source+n);count-=n;
    }
}

/* Command 1 copies 32-byte groups; OUTI and DJNZ both decrement B. Command
   2 copies descriptor rectangles and consumes its mutable row counter. */
void gaw_video_flush_queue(uint8_t bank){
    write_byte(gaw_ram_read16le(0xC034u),0);
    uint16_t q=0xDD00u;
    for(unsigned commands=0;commands<512u;++commands){
        uint8_t command=read_byte(bank,q,0);
        if(command==0){gaw_ram_write16le(0xC034u,0xDD00);gaw_ram_write8(0xDD00u,0);return;}
        if(command==1u){
            uint8_t selected=read_byte(bank,(uint16_t)(q+1u),0),groups=read_byte(bank,(uint16_t)(q+6u),0);
            uint16_t source=read_word(bank,(uint16_t)(q+2u)),destination=read_word(bank,(uint16_t)(q+4u));
            if(!(selected&0x80u))bank=selected;
            address(destination);copy(bank,source,(groups?groups:256u)*32u,(selected&0x80u)!=0);q=(uint16_t)(q+7u);
        }else{
            uint16_t source=read_word(bank,(uint16_t)(q+3u));
            unsigned rows=read_byte(bank,(uint16_t)(q+1u),0);if(!rows)rows=256u;
            unsigned bytes=(uint8_t)(2u*read_byte(bank,(uint16_t)(q+2u),0));if(!bytes)bytes=256u;
            while(rows--){address((uint16_t)(source+0xA200u));copy(bank,source,bytes,0);source=(uint16_t)(source+0x40u);write_byte((uint16_t)(q+1u),(uint8_t)rows);}
            q=(uint16_t)(q+5u);
        }
    }
}
/* Original synchronous IRQ presentation; scanline timing is the backend's
   responsibility. Audio and the asynchronous/line IRQ paths are separate. */
void gaw_video_present_vblank(void){
    for(unsigned i=0;i<3u;++i)address((uint16_t)(((0x8Au-i)<<8)|gaw_ram_read8((uint16_t)(0xC01Au-i))));
    uint8_t bank=4;address(0x7F00u);copy(bank,0xDD40u,64,0);address(0x7F80u);copy(bank,0xDD80u,128,0);
    uint8_t resource=gaw_ram_read8(0xC042u);
    if(resource){
        bank=resource;uint16_t source=gaw_ram_read16le(0xC043u);unsigned count=read_byte(bank,source++,0);if(!count)count=256u;
        gaw_ram_write8(0xC042u,0);address(0x7E00u);
        while(count--)for(unsigned row=0;row<8u;++row){copy(bank,source,3,0);source=(uint16_t)(source+3u);gaw_sms_vdp_data_write(0);}
    }
    if(!gaw_ram_read8(0xC033u)){
        uint8_t phase=gaw_ram_read8(0xC045u)&3u;
        if(phase){uint8_t offset=(uint8_t)((phase<<6)+2u);bank=4;gaw_ram_write8(0xC045u,0);address((uint16_t)(0x7D00u+offset));copy(bank,(uint16_t)(0xDB00u+offset),60,0);}
        address(0xC000u);copy(bank,0xDCA0u,32,0);
    }
    gaw_video_flush_queue(bank);
}
