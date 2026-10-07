#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_effects.h"
#include "gaw_assets.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[GAW_RAM_SIZE],video[0x4000],cram[32],regs[16],sram[0x8000];
static unsigned frames,observed,reference_mode,current_slot;
static uint8_t frame_ram[128][0x1F80],frame_video[128][0x4000];
static void observe(void){
    assert(observed<128u);
    if(reference_mode){memcpy(frame_ram[observed],gaw_ram,0x1F80);memcpy(frame_video[observed],gaw_sms_vram(),0x4000);}
    else {unsigned differences=0;for(unsigned i=0;i<0x1F80u;++i)if(frame_ram[observed][i]!=gaw_ram[i]){if(differences++<25u)fprintf(stderr,"effect trace frame%u RAM%04X ref%02X native%02X\n",observed,0xC000u+i,frame_ram[observed][i],gaw_ram[i]);}assert(differences==0);assert(memcmp(frame_video[observed],gaw_sms_vram(),0x4000)==0);}
    ++observed;
}
static void setup(unsigned mode,unsigned kind,unsigned frame,unsigned corner){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*3u));
    gaw_ram_write8(0xC040,(uint8_t)mode);gaw_ram_write8(0xC066,(uint8_t)(15u-mode));gaw_ram_write16le(0xC0B9,(uint16_t)(mode==2?0x101:0x95));
    gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC02F,(uint8_t)frame);
    gaw_ram_write8(0xC0DA,24);gaw_ram_write8(0xC0DC,16);gaw_ram_write8(0xC0E0,2);gaw_ram_write8(0xC0E1,1);
    gaw_ram_write8(0xC0DF,6);gaw_ram_write8(0xC0E6,(uint8_t)kind);gaw_ram_write8(0xC318,16);gaw_ram_write8(0xC300,2);gaw_ram_write8(0xC301,1);
    gaw_ram_write8(0xC311,(uint8_t)(corner?2:0x58));gaw_ram_write8(0xC313,(uint8_t)(corner?0xFA:0x88));
    gaw_ram_write16le(0xC308,0x80A0);gaw_ram_write8(0xC303,1);
    for(unsigned i=0;i<16u;++i){uint16_t e=(uint16_t)(0xC600u+i*0x30u);gaw_ram_write8(e,(uint8_t)(i?32:0));gaw_ram_write8((uint16_t)(e+3u),(uint8_t)(i&2u));gaw_ram_write8((uint16_t)(e+0x1Bu),(uint8_t)(i%3u));gaw_ram_write8((uint16_t)(e+0x1Au),(uint8_t)(i*5u));gaw_ram_write8((uint16_t)(e+0x1Du),0xFA);}
    for(unsigned i=0;i<0xA0u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(i%32u));
    gaw_ram_write8((uint16_t)(0xC090u+current_slot*8u),(uint8_t)kind);
}
int main(void){
    unsigned cases=0;
    for(current_slot=0;current_slot<2u;++current_slot)for(unsigned mode=0;mode<3u;++mode)for(unsigned kind=1;kind<=2u;++kind)for(unsigned phase=0;phase<3u;++phase)for(unsigned corner=0;corner<2u;++corner){
        unsigned frame=phase==2?255:phase*7u;
        reference_mode=1;observed=0;setup(mode,kind,frame,corner);gaw_host_set_frame_observer(observe);assert(gaw_sms_compat_indexed_call(1,kind==1?0x6AFB:0x6C2E,(uint16_t)(0xC090u+current_slot*8u)));assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);frames=gaw_host_frame_count();for(unsigned i=0;i<0x8000u;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        reference_mode=0;observed=0;setup(mode,kind,frame,corner);gaw_host_set_frame_observer(observe);assert(gaw_effect_native_step((uint16_t)(0xC090u+current_slot*8u)));
        for(unsigned i=0;i<0x1F80u;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"effect %u/%u/%u/%u RAM %04X ref%02X native%02X\n",mode,kind,frame,corner,0xC000u+i,ram[i],gaw_ram[i]);assert(0);}
        for(unsigned i=0;i<0x4000u;++i)if(video[i]!=gaw_sms_vram()[i]){fprintf(stderr,"effect VRAM %04X ref%02X native%02X\n",i,video[i],gaw_sms_vram()[i]);assert(0);}
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<0x8000u;++i){assert(sram[i]==gaw_platform_sram_read((uint16_t)i));}
        if(frames!=gaw_host_frame_count()){fprintf(stderr,"effect frames ref%u native%u\n",frames,gaw_host_frame_count());assert(0);}++cases;
    }
    printf("native full-screen effect differential tests: OK (%u complete cycles)\n",cases);return 0;
}
