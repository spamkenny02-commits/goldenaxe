#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_menu.h"
#include "gaw_player.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16],sram[0x8000];
static unsigned reference,observed,total,case_now;
static FILE *trace;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"ending case%u frame%u RAM%04X ref%02X native%02X\n",case_now,observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){fprintf(stderr,"ending case%u frame%u VRAM%04X ref%02X native%02X\n",case_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);}
}
static void observe(void){
    assert(observed<10000u);
    if(reference){assert(fwrite(gaw_ram,sizeof ram,1,trace)==1);assert(fwrite(gaw_sms_vram(),sizeof video,1,trace)==1);assert(fwrite(gaw_sms_cram(),sizeof cram,1,trace)==1);assert(fwrite(gaw_sms_vdp_regs(),sizeof regs,1,trace)==1);}
    else{
        assert(observed<total);assert(fread(ram,sizeof ram,1,trace)==1);assert(fread(video,sizeof video,1,trace)==1);assert(fread(cram,sizeof cram,1,trace)==1);assert(fread(regs,sizeof regs,1,trace)==1);
        compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
    }
    ++observed;gaw_host_set_pad((uint8_t)(gaw_ram_read8(0xDCC1u)&&observed%4u==0u?0x20:0));
}
static void setup(void){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*7u+case_now));
    gaw_ram_write8(0xC040u,(uint8_t)(case_now&1u?2:0));gaw_ram_write8(0xC0BAu,(uint8_t)(case_now&1u));gaw_ram_write8(0xC066u,(uint8_t)(case_now&1u?13:15));gaw_ram_write16le(0xC034u,0xDD00);gaw_assets_restore_scene();
    memset(gaw_ram_ptr(0xDC00u),3,0xA0);gaw_ram_write16le(0xC0B9u,0x95);gaw_ram_write16le(0xC0A4u,0xB761);
    gaw_ram_write8(0xC0F1u,1);gaw_ram_write8(0xC0F2u,1);gaw_ram_write8(0xC0DFu,0);gaw_ram_write8(0xC0E0u,1);gaw_ram_write8(0xC0DAu,24);gaw_ram_write8(0xC0DCu,16);gaw_ram_write8(0xC0DBu,8);
    gaw_player_init_from_world();gaw_ram_write8(0xC311u,(uint8_t)(case_now>=2u?0x48:0x50));gaw_ram_write8(0xC313u,(uint8_t)(case_now>=2u?0x78:0x80));gaw_ram_write8(0xC318u,20);gaw_ram_write8(0xC01Du,0x0E);gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write8(0xC02Fu,(uint8_t)(case_now*73u));
    gaw_host_queue_pause(12);gaw_host_set_frame_observer(observe);
}
int main(void){
    unsigned cases=0;
    for(case_now=0;case_now<4u;++case_now){
        trace=tmpfile();assert(trace);reference=1;observed=0;setup();assert(gaw_sms_compat_raw_call_args(1,0x6EBE,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        assert(fwrite(gaw_ram,sizeof ram,1,trace)==1);assert(fwrite(gaw_sms_vram(),sizeof video,1,trace)==1);assert(fwrite(gaw_sms_cram(),sizeof cram,1,trace)==1);assert(fwrite(gaw_sms_vdp_regs(),sizeof regs,1,trace)==1);
        for(unsigned i=0;i<sizeof sram;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        rewind(trace);reference=0;observed=0;setup();gaw_dispatch_state_once();assert(observed==total);assert(gaw_host_frame_count()==total);
        assert(fread(ram,sizeof ram,1,trace)==1);assert(fread(video,sizeof video,1,trace)==1);assert(fread(cram,sizeof cram,1,trace)==1);assert(fread(regs,sizeof regs,1,trace)==1);compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<sizeof sram;++i)assert(sram[i]==gaw_platform_sram_read((uint16_t)i));
        assert(gaw_ram_read8(0xC01Du)==0);fclose(trace);++cases;
    }
    printf("native ending differential tests: OK (%u complete credit sequences)\n",cases);return 0;
}
