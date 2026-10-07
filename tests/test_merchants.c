#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_menu.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16],sram[0x8000];
static uint8_t trace_ram[2048][0x1F80],trace_video[2048][0x4000],trace_regs[2048][16];
static unsigned reference,observed,total,case_now,scenario,section,automate,variant_now;
static unsigned selected,confirmed;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"services %u/%u scenario%u frame%u RAM%04X ref%02X native%02X\n",section,case_now,scenario,observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){fprintf(stderr,"services %u/%u frame%u VRAM%04X ref%02X native%02X\n",section,case_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);}
}
static void capture(void){memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);for(unsigned i=0;i<sizeof sram;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);}
static void compare(void){compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);for(unsigned i=0;i<sizeof sram;++i)if(sram[i]!=gaw_platform_sram_read((uint16_t)i)){fprintf(stderr,"services %u/%u variant%u SRAM%04X ref%02X native%02X\n",section,case_now,variant_now,i,sram[i],gaw_platform_sram_read((uint16_t)i));assert(0);}}
static void observe(void){
    assert(observed<2048u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);compare_video(trace_video[observed]);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
    if(automate){
        uint8_t pad=0;
        if(observed%4u==0u && gaw_ram_read8(0xC0A1u)){
            if(confirmed)pad=0x10;
            else if(gaw_ram_read8(0xC0A0u)<selected)pad=2;
            else {pad=0x20;confirmed=1;}
        }
        gaw_host_set_pad(pad);
    }
}
static void setup(unsigned kind,uint8_t cell,unsigned variant){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,0);
    for(unsigned slot=0;slot<3u;++slot)for(unsigned i=0;i<slot*3u+variant%2u;++i)gaw_platform_sram_write((uint16_t)(0x0400u+slot*0x400u+i),(uint8_t)('A'+slot));
    gaw_ram_write8(0xDFFCu,(uint8_t)(variant&1u?4:0));gaw_ram_write8(0xC066u,15);gaw_ram_write16le(0xC034u,0xDD00);gaw_assets_restore_scene();
    for(unsigned i=0;i<0xA0u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(i%16u));
    for(unsigned i=0;i<8u;++i)gaw_ram_write8((uint16_t)(0xC0B0u+i),(uint8_t)('A'+i));
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write8(0xC01Du,0x16);gaw_ram_write8(0xC0A7u,(uint8_t)kind);
    gaw_ram_write16le(0xC0B9u,0x95);gaw_ram_write16le(0xC0BBu,cell);gaw_ram_write8(0xC0DAu,(uint8_t)(variant>=2u?72:24));gaw_ram_write8(0xC0DCu,48);gaw_ram_write8(0xC0DBu,8);gaw_ram_write8(0xC318u,20);
    gaw_ram_write8(0xC0F1u,1);gaw_ram_write8(0xC0F2u,(uint8_t)(variant?variant:1));gaw_ram_write8(0xC0DDu,(uint8_t)(variant?250:0));gaw_ram_write8(0xC0DFu,1);gaw_ram_write8(0xC0E0u,1);gaw_ram_write8(0xC0E1u,1);gaw_ram_write8(0xC0E8u,(uint8_t)(variant&1u));
    for(unsigned i=0;i<9u;++i)gaw_ram_write8((uint16_t)(0xC0CFu+i),(uint8_t)(variant>=2u?0x80:0));
    gaw_ram_write8(0xC0E4u,(uint8_t)(variant%3u));gaw_ram_write8(0xC0E5u,(uint8_t)(variant%3u));gaw_ram_write8(0xC0E6u,(uint8_t)(variant%3u));gaw_ram_write8(0xC0E7u,(uint8_t)(variant&1u));
    gaw_ram_write8(0xC0F3u,(uint8_t)(variant&1u));gaw_ram_write8(0xC0F4u,(uint8_t)(variant&1u));gaw_ram_write8(0xC0DEu,(uint8_t)(variant>=2u?99:3));
    gaw_host_set_frame_observer(observe);
}

static uint8_t byte(uint16_t a){return gaw_sms_rom_bank_read(1,a);}
static uint8_t price(uint8_t cell,unsigned choice){
    for(unsigned i=0;i<5u;++i)if(byte(0x752Eu+i)==cell)return byte(0x7533u+i);
    for(unsigned i=0;i<4u;++i)if(byte(0x75A8u+i)==cell)return byte(0x75AFu+choice);
    unsigned type=0;for(unsigned i=0;i<14u;++i)if(byte(0x796Au+i*2u)==cell){type=byte(0x796Bu+i*2u);break;}
    return byte((uint16_t)(0x7986u+type*14u+(choice*2u+1u)*2u+1u));
}
static void prepare(uint8_t cell,unsigned variant){
    setup(1,cell,0);confirmed=0;
    unsigned cost=price(cell,selected);
    gaw_ram_write8(0xC0DDu,(uint8_t)(variant==0u?0u:variant==1u?cost-1u:variant==2u?cost:255u));
    if(variant==4u){gaw_ram_write8(0xC0E2u,1);gaw_ram_write8(0xC0E8u,1);gaw_ram_write8(0xC0E9u,1);gaw_ram_write8(0xC0F2u,2);}
    if(variant==5u){gaw_ram_write8(0xC0DEu,99);gaw_ram_write8(0xC318u,24);gaw_ram_write8(0xC0DBu,48);gaw_ram_write8(0xC0F2u,3);}
    gaw_host_set_pad(0);
}
int main(void){
    const uint8_t shops[]={0x34,0x5E,0x72,0xF0,0xFC,0x23,0x7B,0xC3,0xDC,0x2E,0x4E,0x53,0x55,0x57,0x71,0x8D,0x94,0xA5,0xC7,0xD7,0xF2,0xF9,0xFE};
    section=5;automate=1;scenario=0;
    for(unsigned shop=0;shop<sizeof shops;++shop)for(selected=0;selected<(shop<5u?1u:3u);++selected)for(variant_now=0;variant_now<6u;++variant_now){
        reference=1;observed=0;prepare(shops[shop],variant_now);
        assert(gaw_sms_compat_raw_call_args(1,0x7390,0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;capture();
        reference=0;observed=0;prepare(shops[shop],variant_now);gaw_dispatch_state_once();compare();assert(observed==total);
        assert(gaw_ram_read8(0xC01Du)==0x0Cu);++case_now;
    }
    printf("native merchant differential tests: OK (%u complete purchases/refusals across 23 shops)\n",case_now);return 0;
}
