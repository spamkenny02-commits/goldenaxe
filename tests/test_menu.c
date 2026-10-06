#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_menu.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16];
static uint8_t trace_ram[512][0x1F80],trace_video[512][0x4000],trace_regs[512][16];
static unsigned reference,observed,total,scenario,case_now;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"menu case%u scenario%u frame%u RAM%04X ref%02X native%02X\n",case_now,scenario,observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){fprintf(stderr,"menu case%u frame%u VRAM%04X ref%02X native%02X\n",case_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);}
}
static void capture(void){memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);}
static void compare(void){compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);}
static void observe(void){
    assert(observed<512u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);compare_video(trace_video[observed]);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
}
static void setup_helper(unsigned selected,unsigned offset,uint8_t held,uint8_t pressed,uint16_t repeat,unsigned pattern){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write8(0xC01Du,0x12);gaw_ram_write8(0xC0A0u,(uint8_t)selected);gaw_ram_write8(0xD120u,(uint8_t)offset);gaw_ram_write16le(0xD121u,repeat);
    gaw_ram_write8(0xC020u,held);gaw_ram_write8(0xC021u,pressed);
    for(unsigned i=0;i<8u;++i){uint8_t glyph=gaw_sms_rom_bank_read(3,(uint16_t)(0x8B48u+(pattern?i:0)));gaw_ram_write16le((uint16_t)(0xD81Cu+i*2u),(uint16_t)(0x0800u|glyph));}
}
static void setup_full(void){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write8(0xC01Du,0x12);gaw_ram_write16le(0xC034u,0xDD00);
    for(unsigned i=0;i<32u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),(uint8_t)((scenario*11u+i*scenario)&63u));
    if(scenario&1u){gaw_host_queue_pad(30,2);gaw_host_queue_pad(31,0);gaw_host_queue_pad(32,8);gaw_host_queue_pad(33,0);}
    unsigned frame=40;
    for(unsigned i=0;i<(scenario&2u?3u:0u);++i){gaw_host_queue_pad(frame,0x20);gaw_host_queue_pad(frame+1u,0);frame+=2u;}
    if(scenario&2u){gaw_host_queue_pad(frame,0x10);gaw_host_queue_pad(frame+1u,0);frame+=2u;}
    for(unsigned i=0;i<10u;++i){gaw_host_queue_pad(frame,0x20);gaw_host_queue_pad(frame+1u,0);frame+=2u;}
    for(;frame<500u;frame+=8u){gaw_host_queue_pad(frame,0x20);gaw_host_queue_pad(frame+1u,0);}
    gaw_host_queue_pause(12);gaw_host_set_frame_observer(observe);
}
int main(void){
    unsigned cursor_cases=0,input_cases=0,full_cases=0;
    const uint16_t repeats[]={0,0x1700,0x0701,0xFF01};
    for(unsigned selected=0;selected<42u;++selected)for(unsigned pressed=0;pressed<16u;++pressed)for(unsigned held=0;held<3u;++held)for(unsigned repeat=0;repeat<4u;++repeat){
        case_now=cursor_cases;setup_helper(selected,selected%8u*2u,(uint8_t)(held==0u?0:held==1u?pressed:15u),(uint8_t)pressed,repeats[repeat],1);
        assert(gaw_sms_compat_raw_call_args(0,0x12C1,0,0,0,0));assert(gaw_sms_compat_faults()==0);capture();
        setup_helper(selected,selected%8u*2u,(uint8_t)(held==0u?0:held==1u?pressed:15u),(uint8_t)pressed,repeats[repeat],1);gaw_name_cursor();compare();++cursor_cases;
    }
    const uint8_t buttons[]={0,0x10,0x20,0x30};
    for(unsigned selected=0;selected<42u;++selected)for(unsigned offset=0;offset<8u;++offset)for(unsigned button=0;button<4u;++button)for(unsigned pattern=0;pattern<2u;++pattern){
        case_now=input_cases;setup_helper(selected,offset*2u,0,buttons[button],0,pattern);
        assert(gaw_sms_compat_raw_call_args(0,0x11BA,0,0,0,0));assert(gaw_sms_compat_faults()==0);capture();
        setup_helper(selected,offset*2u,0,buttons[button],0,pattern);gaw_name_input();compare();++input_cases;
    }
    for(scenario=0;scenario<4u;++scenario){
        reference=1;observed=0;setup_full();assert(gaw_sms_compat_raw_call_args(0,0x1101,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;capture();
        reference=0;observed=0;setup_full();gaw_dispatch_state_once();compare();assert(observed==total);assert(gaw_host_frame_count()==total);assert(gaw_ram_read8(0xC01Du)==4u);++full_cases;
    }
    printf("native name-entry differential tests: OK (%u cursor + %u input + %u complete cycles)\n",cursor_cases,input_cases,full_cases);return 0;
}
