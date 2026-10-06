#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_presentation.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16];
static uint16_t q;
static void append(uint8_t value){gaw_ram_write8(q++,value);}
static void block(uint8_t bank,uint16_t source,uint16_t destination,uint8_t groups){append(1);append(bank);append((uint8_t)source);append((uint8_t)(source>>8));append((uint8_t)destination);append((uint8_t)(destination>>8));append(groups);}
static void rect(uint8_t rows,uint8_t columns,uint16_t source){append(2);append(rows);append(columns);append((uint8_t)source);append((uint8_t)(source>>8));}
static void setup(unsigned kind,unsigned frozen,unsigned phase,unsigned glyph){
    gaw_platform_init();gaw_sms_compat_reset();
    for(unsigned i=0;i<GAW_RAM_SIZE;++i)gaw_ram[i]=(uint8_t)(i*13u+kind*7u);
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*3u+phase));
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*5u+11u+(i>>14)*41u));
    gaw_ram_write8(0xDFFCu,0); /* original queue's primary SRAM page */
    gaw_ram_write8(0xC033u,(uint8_t)frozen);gaw_ram_write8(0xC045u,(uint8_t)phase);gaw_ram_write8(0xC042u,(uint8_t)(glyph?4:0));gaw_ram_write16le(0xC043u,0xA241);
    memset(gaw_ram_ptr(0xDD00u),0,64);q=0xDD00;
    if(kind==1u)block(0xFF,0xD200,0x5000,1);
    if(kind==2u)block(15,0x8000,0x5100,2);
    if(kind==3u)block(0xFF,0x9000,0x6000,2);
    if(kind==4u)rect(3,5,0xD6E4);
    if(kind==5u){rect(2,3,0xD9C0);block(10,0x87F0,0x5FE0,3);block(0xFF,0x9000,0x6600,2);block(0xFF,0xD100,0x7770,1);}
    if(kind==6u)block(0xFF,0x8000,0x5000,0);
    if(kind==7u)rect(0,0,0xD600);
    gaw_ram_write16le(0xC034u,q);
}
static void compare(unsigned section,unsigned kind,unsigned frozen,unsigned phase,unsigned glyph){
    for(unsigned i=0;i<sizeof ram;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"presentation %u/%u/%u/%u/%u RAM%04X ref%02X native%02X\n",section,kind,frozen,phase,glyph,0xC000u+i,ram[i],gaw_ram[i]);assert(0);}
    for(unsigned i=0;i<sizeof video;++i)if(video[i]!=gaw_sms_vram()[i]){fprintf(stderr,"presentation %u/%u/%u/%u/%u VRAM%04X ref%02X native%02X\n",section,kind,frozen,phase,glyph,i,video[i],gaw_sms_vram()[i]);assert(0);}
    assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);assert(gaw_host_frame_count()==0);
}
int main(void){
    unsigned cases=0;
    for(unsigned section=0;section<2u;++section)for(unsigned kind=0;kind<8u;++kind)for(unsigned frozen=0;frozen<2u;++frozen)for(unsigned phase=0;phase<4u;++phase)for(unsigned glyph=0;glyph<2u;++glyph){
        setup(kind,frozen,phase,glyph);
        assert(section?gaw_sms_compat_irq_video_call():gaw_sms_compat_raw_call_args(4,0x0293,0,0,0,0));assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        setup(kind,frozen,phase,glyph);if(section)gaw_video_present_vblank();else gaw_video_flush_queue(4);compare(section,kind,frozen,phase,glyph);++cases;
    }
    printf("native IRQ video/queue differential tests: OK (%u cases)\n",cases);return 0;
}
