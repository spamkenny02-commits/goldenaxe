#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16],sram[0x8000];
static uint8_t trace_ram[40][0x1F80],trace_video[40][0x4000],trace_regs[40][16];
static unsigned reference,observed,total,layer_now,selection_now,scenario_now,variant_now;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"inventory %u/%u/%u/%u frame%u RAM%04X ref%02X native%02X\n",layer_now,selection_now,scenario_now,variant_now,observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){fprintf(stderr,"inventory %u/%u/%u/%u frame%u VRAM%04X ref%02X native%02X\n",layer_now,selection_now,scenario_now,variant_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);}
}
static void observe(void){
    assert(observed<40u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);compare_video(trace_video[observed]);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
}
static void setup(void){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*7u+variant_now));
    for(unsigned i=0;i<256u;++i){gaw_ram_write8((uint16_t)(0xC100u+i),(uint8_t)(variant_now&1u?0x10:((i%3u)?0x10:0)));gaw_ram_write8((uint16_t)(0xC200u+i),0xFF);}
    gaw_ram_write8(0xC040u,(uint8_t)layer_now);gaw_ram_write16le(0xC0B9u,(uint16_t)(layer_now==0u?0x95:layer_now==1u?0x101:0x12F));
    gaw_ram_write8(0xC0BAu,(uint8_t)(layer_now!=0u));gaw_ram_write8(0xC037u,(uint8_t)(variant_now>>1));
    gaw_ram_write8(0xC066u,(uint8_t)(15u-layer_now));gaw_ram_write16le(0xC034u,0xDD00);gaw_assets_restore_scene();
    for(unsigned i=0;i<0xA0u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(i%16u));
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write8(0xC01Du,0x10);
    gaw_ram_write8(0xC02Fu,(uint8_t)(variant_now?0xFD:0));gaw_ram_write8(0xC0DAu,24);gaw_ram_write8(0xC0DCu,16);gaw_ram_write8(0xC0DBu,8);
    gaw_ram_write8(0xC300u,2);gaw_ram_write8(0xC303u,1);gaw_ram_write16le(0xC308u,0x8495);gaw_ram_write8(0xC311u,0x58);gaw_ram_write8(0xC313u,0x88);gaw_ram_write8(0xC318u,20);
    gaw_ram_write8(0xC0F1u,(uint8_t)(1u+variant_now%2u));gaw_ram_write8(0xC0F2u,(uint8_t)(1u+variant_now%3u));gaw_ram_write8(0xC0DFu,(uint8_t)selection_now);
    for(unsigned i=0;i<17u;++i)gaw_ram_write8((uint16_t)(0xC0E0u+i),(uint8_t)(variant_now&1u?1u:(i%2u)));
    gaw_ram_write8(0xC0DEu,(uint8_t)(variant_now*85u));
    if(scenario_now==1u){gaw_host_queue_pad(4,0x0C);gaw_host_queue_pad(5,0);gaw_host_queue_pad(6,3);gaw_host_queue_pad(7,0);}
    if(scenario_now==2u){gaw_host_queue_pad(4,8);gaw_host_queue_pad(5,0);gaw_host_queue_pad(6,2);gaw_host_queue_pad(7,0);gaw_host_queue_pad(8,4);gaw_host_queue_pad(9,0);}
    gaw_host_queue_pad(10,0x20);gaw_host_queue_pad(11,0);gaw_host_queue_pad(14,0x10);gaw_host_queue_pause(8);gaw_host_set_frame_observer(observe);
}
int main(void){
    unsigned cases=0;
    for(layer_now=0;layer_now<3u;++layer_now)for(selection_now=0;selection_now<12u;++selection_now)for(scenario_now=0;scenario_now<3u;++scenario_now)for(variant_now=0;variant_now<4u;++variant_now){
        reference=1;observed=0;setup();assert(gaw_sms_compat_raw_call_args(1,0x70F2,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        for(unsigned i=0;i<sizeof sram;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        reference=0;observed=0;setup();gaw_dispatch_state_once();compare_ram(ram);compare_video(video);
        assert(observed==total);assert(gaw_host_frame_count()==total);assert(gaw_ram_read8(0xC01Du)==0x0C);
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<sizeof sram;++i)assert(sram[i]==gaw_platform_sram_read((uint16_t)i));
        ++cases;
    }
    printf("native inventory differential tests: OK (%u complete cycles)\n",cases);return 0;
}
