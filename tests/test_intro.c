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
static unsigned skipped,seen_picker,canceled,refused;
static FILE *trace;
static void compare_ram(const uint8_t *expected){
    unsigned differences=0;
    for(unsigned i=0;i<sizeof ram;++i)if(i!=0x2Au&&i!=0x2Bu&&expected[i]!=gaw_ram[i]){if(differences++<20u)fprintf(stderr,"intro case%u frame%u RAM%04X ref%02X native%02X\n",case_now,observed,0xC000u+i,expected[i],gaw_ram[i]);}
    assert(differences==0);
}
static void compare_video(const uint8_t *expected){
    for(unsigned i=0;i<sizeof video;++i)if(expected[i]!=gaw_sms_vram()[i]){fprintf(stderr,"intro case%u frame%u VRAM%04X ref%02X native%02X\n",case_now,observed,i,expected[i],gaw_sms_vram()[i]);assert(0);}
}
static void observe(void){
    assert(observed<12000u);
    if(reference){assert(fwrite(gaw_ram,sizeof ram,1,trace)==1);assert(fwrite(gaw_sms_vram(),sizeof video,1,trace)==1);assert(fwrite(gaw_sms_cram(),sizeof cram,1,trace)==1);assert(fwrite(gaw_sms_vdp_regs(),sizeof regs,1,trace)==1);}
    else{
        assert(observed<total);assert(fread(ram,sizeof ram,1,trace)==1);assert(fread(video,sizeof video,1,trace)==1);assert(fread(cram,sizeof cram,1,trace)==1);assert(fread(regs,sizeof regs,1,trace)==1);
        compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
    }
    ++observed;uint8_t pad=0;
    if(case_now<6u&&case_now){
        static const unsigned skip_after[]={0,10,1000,2000,3000,4100};
        if(!skipped&&observed>=skip_after[case_now]){pad=0x20;skipped=1;}
        else if(gaw_ram_read16le(0xC02Cu)==0x0280u&&observed%4u==0u)pad=0x20;
        else if(gaw_ram_read8(0xC065u)==0x89u&&observed%4u==0u)pad=0x20;
    }else if(case_now>=6u){
        unsigned picker=gaw_ram_read16le(0xD65Au)==0x08A8u;
        if(picker)seen_picker=1;
        if(seen_picker&&!picker)canceled=1;
        if(gaw_ram_read8(0xDE08u)==0xA1u)refused=1;
        if(observed%4u==0u){
            if(case_now>=16u&&picker){
                if(case_now<18u)pad=0x10;
                else pad=gaw_ram_read8(0xC0A0u)<3u?2:0x20;
            }else if(canceled)pad=gaw_ram_read8(0xC0A0u)?1:0x20;
            else if(case_now>=12u&&picker&&refused&&gaw_ram_read8(0xC0A0u)==0)pad=2;
            else pad=0x20;
        }
    }
    gaw_host_set_pad(pad);
}
static void setup(void){
    skipped=seen_picker=canceled=refused=0;gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);gaw_video_initialize_native();
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*7u+case_now));
    gaw_ram_write16le(0xC034u,0xDD00);gaw_ram_write8(0xC011u,0xE0);gaw_ram_write16le(0xC02Cu,0x0263);
    for(unsigned i=0;i<32u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),(uint8_t)((i*case_now+case_now*11u)&63u));
    gaw_ram_write8(0xC01Du,0);gaw_ram_write8(0xC02Fu,(uint8_t)(case_now*73u));gaw_ram_write8(0xDFFCu,(uint8_t)(case_now&1u?4:0));
    if(case_now>=6u){
        unsigned slot=case_now<12u?(case_now-6u)/2u:case_now<16u?0:2;
        gaw_ram_write8(0xC036u,(uint8_t)(slot+1u));
        uint16_t page=(case_now&1u)?0x4000u:0u;
        for(unsigned i=0;i<3u;++i){
            uint16_t base=(uint16_t)(page+0x400u+i*0x400u);
            for(unsigned j=0;j<8u;++j)gaw_platform_sram_write((uint16_t)(base+j),(uint8_t)(j<4u?'A'+i:0));
        }
        if(case_now>=12u&&case_now<16u)gaw_platform_sram_write((uint16_t)(page+0x400u),0);
    }
    gaw_host_queue_pause(12);gaw_host_set_frame_observer(observe);
}

int main(void){
    unsigned cases=0;
    for(case_now=0;case_now<20u;++case_now){
        trace=tmpfile();assert(trace);reference=1;observed=0;setup();assert(gaw_sms_compat_raw_call_args(0,(uint16_t)(case_now<6u?0x146D:0x14ED),0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        assert(fwrite(gaw_ram,sizeof ram,1,trace)==1);assert(fwrite(gaw_sms_vram(),sizeof video,1,trace)==1);assert(fwrite(gaw_sms_cram(),sizeof cram,1,trace)==1);assert(fwrite(gaw_sms_vdp_regs(),sizeof regs,1,trace)==1);
        for(unsigned i=0;i<sizeof sram;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        rewind(trace);reference=0;observed=0;setup();if(case_now<6u)gaw_dispatch_state_once();else gaw_title_choose();assert(observed==total);assert(gaw_host_frame_count()==total);
        assert(fread(ram,sizeof ram,1,trace)==1);assert(fread(video,sizeof video,1,trace)==1);assert(fread(cram,sizeof cram,1,trace)==1);assert(fread(regs,sizeof regs,1,trace)==1);compare_ram(ram);compare_video(video);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        for(unsigned i=0;i<sizeof sram;++i)assert(sram[i]==gaw_platform_sram_read((uint16_t)i));
        assert(gaw_ram_read8(0xC01Du)==(!case_now?0u:case_now<6u||case_now>=16u?0x12u:6u));
        if(case_now>=12u&&case_now<16u)assert(refused);
        if(case_now>=16u)assert(canceled);
        fclose(trace);++cases;
    }
    printf("native intro differential tests: OK (%u complete intro/title/new/continue/cancel cycles)\n",cases);return 0;
}
