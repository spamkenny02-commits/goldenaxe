#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_ui.h"
#include "gaw_ram.h"
#include "gaw_video.h"
#include "gaw_sms_compat.h"
#include "gaw_platform.h"
#include "gaw_host.h"
static uint8_t ram[0x1F80],video[0x4000],cram[32],regs[16];
static uint8_t trace_ram[64][0x1F80],trace_video[64][0x4000],trace_regs[64][16];
static unsigned reference,observed,total;
static void compare_ram(const uint8_t *expected){
    for(unsigned i=0;i<sizeof ram;++i)if(expected[i]!=gaw_ram[i]){
        fprintf(stderr,"transition frame%u RAM%04X ref%02X native%02X\n",observed,0xC000u+i,expected[i],gaw_ram[i]);assert(0);
    }
}
static void observe(void){
    assert(observed<64u);
    if(reference){memcpy(trace_ram[observed],gaw_ram,sizeof ram);memcpy(trace_video[observed],gaw_sms_vram(),sizeof video);memcpy(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs);}
    else{assert(observed<total);compare_ram(trace_ram[observed]);assert(memcmp(trace_video[observed],gaw_sms_vram(),sizeof video)==0);assert(memcmp(trace_regs[observed],gaw_sms_vdp_regs(),sizeof regs)==0);}
    ++observed;
}
static void setup(unsigned seed,unsigned flags){
    gaw_platform_init();gaw_sms_compat_reset();
    for(unsigned i=0;i<GAW_RAM_SIZE;++i)gaw_ram[i]=(uint8_t)(i*13u+seed*17u);
    /* Use a valid idle sound workspace; the IRQ now runs the real driver. */
    memset(gaw_ram_ptr(0xDE00u),0,0x190);gaw_ram_write8(0xDE05u,0x80);
    /* The presentation IRQ consumes the queue during each barrier. */
    memset(gaw_ram_ptr(0xDD00u),0,64);gaw_ram_write16le(0xC034u,0xDD00);gaw_ram_write8(0xC042u,0);
    for(unsigned i=0;i<32u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),(uint8_t)((i*seed+seed*11u)&0x3Fu));
    gaw_ram_write8(0xC010u,(uint8_t)(flags&1u?0x16:0x06));gaw_ram_write8(0xC011u,(uint8_t)(flags&2u?0xE0:0x80));
    for(unsigned i=0;i<16u;++i){gaw_sms_vdp_control_write(i<2u?gaw_ram_read8((uint16_t)(0xC010u+i)):(uint8_t)(i*3u));gaw_sms_vdp_control_write((uint8_t)(0x80u+i));}
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*7u+seed));
    gaw_host_queue_pad(2,0x10);gaw_host_queue_pad(8,0);gaw_host_queue_pause(4);gaw_host_set_frame_observer(observe);
}
int main(void){
    const uint16_t addresses[]={0x0AA4,0x0B12,0x1FA7};
    void (*const functions[])(void)={gaw_ui_fade_in,gaw_ui_fade_out,gaw_ui_reveal_world};unsigned cases=0;
    for(unsigned seed=0;seed<4u;++seed)for(unsigned flags=0;flags<4u;++flags)for(unsigned kind=0;kind<3u;++kind){
        reference=1;observed=0;setup(seed,flags);assert(gaw_sms_compat_raw_call_args(0,addresses[kind],0,0,0,0));assert(gaw_sms_compat_faults()==0);total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        reference=0;observed=0;setup(seed,flags);functions[kind]();compare_ram(ram);assert(observed==total);assert(gaw_host_frame_count()==total);
        assert(memcmp(video,gaw_sms_vram(),sizeof video)==0);assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);++cases;
    }
    printf("native display transition differential tests: OK (%u cases)\n",cases);return 0;
}
