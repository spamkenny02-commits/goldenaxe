#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[GAW_RAM_SIZE],video[0x4000],cram[32],regs[16],sram[0x8000];
static void setup(unsigned mode,unsigned cell,unsigned open,unsigned index){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(0xC040,(uint8_t)mode);gaw_ram_write8(0xC066,(uint8_t)(15u-mode));gaw_ram_write16le(0xC0B9,(uint16_t)cell);gaw_ram_write8(0xC0AC,(uint8_t)open);gaw_ram_write8(0xC037,(uint8_t)index);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*7u+1u));
}
int main(void){
    const unsigned cells[]={0x95,0x96,0xAA,0xCB,0x101,0x1BF};unsigned cases=0;
    for(unsigned mode=0;mode<3u;++mode)for(unsigned c=0;c<6u;++c)for(unsigned open=0;open<2u;++open){
        setup(mode,cells[c],open,c);assert(gaw_sms_compat_raw_call_args(0,0x16EF,0,0,0,0));assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);for(unsigned i=0;i<0x8000u;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        setup(mode,cells[c],open,c);gaw_assets_restore_scene();
        for(unsigned i=0;i<0x1F80u;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"scene %u/%u/%u RAM %04X ref%02X native%02X\n",mode,cells[c],open,0xC000u+i,ram[i],gaw_ram[i]);assert(0);}
        assert(memcmp(video,gaw_sms_vram(),sizeof video)==0);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<0x8000u;++i){assert(sram[i]==gaw_platform_sram_read((uint16_t)i));}
        assert(gaw_host_frame_count()==0);++cases;
    }
    printf("native scene asset differential tests: OK (%u cases)\n",cases);return 0;
}
