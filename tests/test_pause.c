#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_ram.h"
#include "gaw_platform.h"
#include "gaw_host.h"
#include "gaw_sms_compat.h"
static uint8_t ram[GAW_RAM_SIZE],video[0x4000],cram[32],regs[16];
static unsigned frames,zero_caps;
static void setup(unsigned item,unsigned delay){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write8(RAM_MAIN_STATE,2);gaw_ram_write8(0xC0DF,(uint8_t)item);
    gaw_ram_write8(0xC0DA,24);gaw_ram_write8(0xC0DC,16);gaw_ram_write8(0xC318,16);gaw_ram_write8(0xC0DB,8);
    gaw_ram_write8(0xC0E0,2);gaw_ram_write8(0xC0E1,1);gaw_ram_write8(0xC311,0x58);gaw_ram_write8(0xC313,0x88);
    for(unsigned i=0;i<0xA0u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(i%16u));
    for(unsigned i=0;i<0x100u;++i)gaw_ram_write8((uint16_t)(0xC900u+i),(uint8_t)(i*5u));
    if(zero_caps){gaw_ram_write8(0xC0DA,0);gaw_ram_write8(0xC0DC,0);gaw_ram_write8(0xC318,0);gaw_ram_write8(0xC0DB,0);}
    gaw_host_queue_pause(delay);
}
int main(void){
    for(unsigned s=0;s<256u;++s)assert(gaw_main_state_is_native((uint8_t)s)==(s==2u||s==10u||s==12u));
    const unsigned delays[]={24,30,80,255};
    for(zero_caps=0;zero_caps<2u;++zero_caps)for(unsigned item=0;item<6u;++item)for(unsigned d=0;d<4u;++d){
        setup(item,delays[d]);assert(gaw_sms_compat_call(0,0x00F4));assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);frames=gaw_host_frame_count();
        setup(item,delays[d]);gaw_dispatch_state_once();
        for(unsigned i=0;i<0x1F80u;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"pause item%u delay%u RAM%04X ref%02X native%02X\n",item,delays[d],0xC000u+i,ram[i],gaw_ram[i]);assert(0);}
        for(unsigned i=0;i<0x4000u;++i)if(video[i]!=gaw_sms_vram()[i]){fprintf(stderr,"pause item%u delay%u VRAM%04X ref%02X native%02X\n",item,delays[d],i,video[i],gaw_sms_vram()[i]);assert(0);}
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);assert(frames==gaw_host_frame_count());
    }
    puts("native pause differential tests: OK (48 complete modal cycles)");return 0;
}
