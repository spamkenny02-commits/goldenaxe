#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_world.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16],sram[0x8000];
static uint8_t trace_ram[80][0x1F80],trace_video[80][0x4000],trace_regs[80][16];
static unsigned reference,observed,total,cell_now,variant_now,state_now;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){
        if(differences++<20u)fprintf(stderr,"entry state%02X cell%03X variant%u frame%u RAM%04X ref%02X native%02X\n",state_now,cell_now,variant_now,observed,0xC000u+i,expected[i],gaw_ram[i]);
    }
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){
        fprintf(stderr,"entry cell%03X variant%u frame%u VRAM%04X ref%02X native%02X\n",cell_now,variant_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);
    }
}
static void observe(void){
    assert(observed<80u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);compare_video(trace_video[observed]);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
}
static void setup(unsigned cell,unsigned variant){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*7u));
    memset(gaw_ram_ptr(0xC200u),0xFF,256);gaw_ram_write16le(0xC0B9u,(uint16_t)cell);gaw_world_select_layer();
    gaw_ram_write8(0xC066u,(uint8_t)(15u-gaw_ram_read8(0xC040u)));gaw_ram_write16le(0xC034u,0xDD00);gaw_assets_restore_scene();
    if(!(variant&1u))gaw_ram_write8(0xC066u,0xFF);
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,(uint8_t)(variant&2u?0xE0:0xA0));
    gaw_ram_write8(0xC01Du,(uint8_t)state_now);gaw_ram_write16le(0xC0C0u,(uint16_t)cell);gaw_ram_write16le(0xC028u,0x7391);gaw_ram_write8(0xC02Fu,0xFF);
    gaw_ram_write8(0xC0DAu,24);gaw_ram_write8(0xC0DCu,16);gaw_ram_write8(0xC318u,20);gaw_ram_write8(0xC311u,0x58);gaw_ram_write8(0xC313u,0x88);
    gaw_ram_write8(0xC0F1u,1);gaw_ram_write8(0xC0F2u,1);gaw_ram_write8(0xC0DFu,1);gaw_ram_write8(0xC0E0u,1);gaw_ram_write8(0xC0E1u,2);
    gaw_host_queue_pad(2,0x10);gaw_host_queue_pad(7,0);gaw_host_queue_pause(5);gaw_host_set_frame_observer(observe);
}
int main(void){
    const unsigned cells[]={0,0x10,0x11,0x19,0x2F,0x55,0x95,0x96,0xBF,0x100,0x101,0x17F,0x1FF};unsigned cases=0;
    for(state_now=4;state_now<=8u;state_now+=2)for(unsigned c=0;c<(state_now==4?sizeof cells/sizeof cells[0]:512u);++c)for(variant_now=0;variant_now<4u;++variant_now){
        cell_now=state_now==4?cells[c]:c;reference=1;observed=0;setup(cell_now,variant_now);
        assert(gaw_sms_compat_raw_call_args(0,state_now==4?0x2433:state_now==6?0x246F:0x24B6,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        uint8_t entropy[64];unsigned count=gaw_sms_compat_refresh_trace(entropy,64);assert(count>0&&count<=64u);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        for(unsigned i=0;i<sizeof sram;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        reference=0;observed=0;setup(cell_now,variant_now);gaw_host_set_entropy_sequence(entropy,count);gaw_dispatch_state_once();
        compare_ram(ram);compare_video(video);assert(observed==total);assert(gaw_host_frame_count()==total);assert(gaw_ram_read8(0xC01Du)==0x0C);
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<sizeof sram;++i){assert(sram[i]==gaw_platform_sram_read((uint16_t)i));}
        ++cases;
    }
    printf("native gameplay entry differential tests: OK (%u complete cycles)\n",cases);return 0;
}
