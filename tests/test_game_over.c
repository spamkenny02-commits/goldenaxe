#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16];
static uint8_t trace_ram[64][0x1F80],trace_video[64][0x4000],trace_regs[64][16];
static unsigned reference,observed,total;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"death menu frame%u RAM%04X ref%02X native%02X\n",observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void observe(void){
    assert(observed<64u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);assert(memcmp(trace_video[observed],gaw_sms_vram(),sizeof video)==0);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
}
static void setup(unsigned palette,unsigned interior,unsigned scenario,uint8_t gold){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*13u+palette));
    for(unsigned i=0;i<32u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),(uint8_t)((palette*17u+i*palette)&63u));
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write8(0xC065u,(uint8_t)(palette&1u?0x8A:0x82));
    gaw_ram_write8(0xC01Du,0x14);gaw_ram_write16le(0xC034u,0xDD00);gaw_ram_write8(0xC0BAu,(uint8_t)interior);
    gaw_ram_write16le(0xC0C2u,0x95);gaw_ram_write16le(0xC0C4u,0x101);gaw_ram_write8(0xC0DDu,gold);
    if(scenario==1u||scenario==2u){gaw_host_queue_pad(26,2);gaw_host_queue_pad(27,0);}
    if(scenario==2u){gaw_host_queue_pad(28,1);gaw_host_queue_pad(29,0);}
    gaw_host_queue_pad(30,(uint8_t)(scenario==3u?0x10:0x20));gaw_host_queue_pause(4);gaw_host_set_frame_observer(observe);
}
int main(void){
    const uint8_t amounts[]={0,3,100,255};unsigned cases=0;
    for(unsigned palette=0;palette<4u;++palette)for(unsigned interior=0;interior<2u;++interior)for(unsigned scenario=0;scenario<4u;++scenario)for(unsigned g=0;g<4u;++g){
        reference=1;observed=0;setup(palette,interior,scenario,amounts[g]);assert(gaw_sms_compat_raw_call_args(0,0x257D,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        reference=0;observed=0;setup(palette,interior,scenario,amounts[g]);gaw_dispatch_state_once();compare_ram(ram);
        assert(observed==total);assert(gaw_host_frame_count()==total);assert(memcmp(video,gaw_sms_vram(),sizeof video)==0);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        assert(gaw_ram_read8(0xC01Du)==(scenario==1u?0u:6u));++cases;
    }
    printf("native game-over menu differential tests: OK (%u complete cycles)\n",cases);return 0;
}
