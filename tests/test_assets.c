#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static unsigned test_item,test_destination;
static uint8_t ram[GAW_RAM_SIZE],video[0x4000],cram[32],regs[16];
static void setup(void){
    gaw_platform_init();gaw_sms_compat_reset();
    for(unsigned i=0;i<GAW_RAM_SIZE;++i)gaw_ram[i]=(uint8_t)(i*7u);
    gaw_sms_vdp_control_write(0);gaw_sms_vdp_control_write(0x40);
    for(unsigned i=0;i<0x4000u;++i)gaw_sms_vdp_data_write((uint8_t)(i*13u+1u));
}
static void capture(void){assert(gaw_sms_compat_faults()==0);memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);}
static void compare(void){for(unsigned i=0;i<0x1F80u;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"item %u dst %04X RAM %04X ref %02X native %02X\n",test_item,test_destination,0xC000u+i,ram[i],gaw_ram[i]);assert(0);}for(unsigned i=0;i<sizeof video;++i)if(video[i]!=gaw_sms_vram()[i]){fprintf(stderr,"item %u dst %04X VRAM %04X ref %02X native %02X\n",test_item,test_destination,i,video[i],gaw_sms_vram()[i]);assert(0);}assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);assert(gaw_host_frame_count()==0);}
int main(void){
    const uint16_t destinations[]={0x5200,0x7780,0x7FC0};
    for(unsigned item=0;item<=0x2Bu;++item)for(unsigned d=0;d<3u;++d){
        test_item=item;test_destination=destinations[d];setup();assert(gaw_sms_compat_raw_call_args(0,0x2AF4,0,destinations[d],0,(uint8_t)item));capture();
        setup();gaw_assets_load_item((uint8_t)item,destinations[d]);compare();
    }
    const uint16_t sources[]={0xA33B,0xAD48,0xA2D2,0xBBB9};
    const uint8_t banks[]={5,5,4,4};
    for(unsigned i=0;i<4u;++i){
        test_item=100+i;test_destination=0x4000;setup();assert(gaw_sms_compat_raw_call_args(0,0x0327,sources[i],0x4000,0,banks[i]));capture();
        setup();(void)gaw_assets_unpack_tiles(banks[i],sources[i],0x4000);compare();
    }
    puts("native asset differential tests: OK (132 item cases + 4 raw Z80 decoders)");return 0;
}
