#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16];
static void setup(unsigned cell,uint8_t mask,unsigned progress){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(0xC0B9u,(uint16_t)cell);gaw_ram_write8((uint16_t)(0xC200u+(cell&0xFFu)),mask);
    gaw_ram_write8(0xC037u,2);gaw_ram_write8(0xC0D0u,(uint8_t)progress);
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*7u+cell));
}
int main(void){
    const uint8_t masks[]={0,0xFF,0xA5,0x3C},progress[]={0,1,0x80};unsigned cases=0;
    for(unsigned cell=0;cell<512u;++cell)for(unsigned m=0;m<4u;++m)for(unsigned p=0;p<3u;++p){
        setup(cell,masks[m],progress[p]);assert(gaw_sms_compat_raw_call_args(0,0x1780,0,0,0,0));assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        setup(cell,masks[m],progress[p]);gaw_world_spawn_map_entities_native();
        for(unsigned i=0;i<sizeof ram;++i)if(ram[i]!=gaw_ram[i]){fprintf(stderr,"map cell%03X mask%02X progress%02X RAM%04X ref%02X native%02X\n",cell,masks[m],progress[p],0xC000u+i,ram[i],gaw_ram[i]);assert(0);}
        for(unsigned i=0;i<sizeof video;++i)if(video[i]!=gaw_sms_vram()[i]){fprintf(stderr,"map cell%03X mask%02X progress%02X VRAM%04X ref%02X native%02X\n",cell,masks[m],progress[p],i,video[i],gaw_sms_vram()[i]);assert(0);}
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);++cases;
    }
    printf("native map entity resource differential tests: OK (%u cases across 512 cells)\n",cases);return 0;
}
