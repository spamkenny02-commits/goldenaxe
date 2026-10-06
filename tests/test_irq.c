#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_audio.h"
#include "gaw_core.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_video.h"

static uint8_t ram[0x1F90], video[0x4000], cram[32], regs[16], entropy[64];
static uint16_t sound[256], actual_sound[256];
static unsigned case_now;
static const uint16_t line_modes[] = {0x0263,0x0275,0x0280};

static void setup(unsigned path, unsigned status, unsigned seed, unsigned mode) {
    gaw_platform_init();
    gaw_sms_compat_reset();
    gaw_audio_reset_diagnostics();
    for (unsigned i=0;i<GAW_RAM_SIZE;++i) gaw_ram[i]=(uint8_t)(i*13u+seed*17u);
    memset(gaw_ram_ptr(0xDE00u),0,0x190);
    gaw_ram_write8(0xDE05u,0x80);
    gaw_ram_write8(0xDE03u,(uint8_t)mode);
    gaw_ram_write8(0xDE06u,(uint8_t)(0x81u+seed%13u));
    for (unsigned i=0;i<seed%64u;++i) gaw_audio_tick();
    gaw_ram_write8(0xDE08u,(uint8_t)(0x90u+seed%29u));
    gaw_ram_write8(0xDFFCu,(uint8_t)(seed&1u?4:0));
    gaw_ram_write8(0xC02Eu,(uint8_t)(path==1u));
    gaw_ram_write8(0xC030u,(uint8_t)(seed%5u));
    gaw_ram_write8(0xC01Cu,(uint8_t)(seed%3u?seed%23u:0));
    gaw_ram_write8(0xC020u,(uint8_t)(seed&63u));
    gaw_ram_write8(0xC022u,(uint8_t)(seed&1u));
    gaw_ram_write8(0xC033u,(uint8_t)(seed&1u));
    gaw_ram_write8(0xC045u,(uint8_t)(seed%4u));
    gaw_ram_write8(0xC042u,(uint8_t)(seed&2u?4:0));
    gaw_ram_write16le(0xC043u,0xA241);
    gaw_ram_write16le(0xC02Cu,line_modes[seed%3u]);
    gaw_ram_write8(0xC010u,(uint8_t)(seed|0x10u));
    gaw_ram_write16le(0xC034u,0xDD07);
    static const uint8_t queue[]={1,15,0,0x80,0,0x50,1,0};
    memcpy(gaw_ram_ptr(0xDD00u),queue,sizeof queue);
    for (unsigned i=0;i<0x4000u;++i) gaw_video_write_at((uint16_t)i,(uint8_t)(i*7u+seed));
    for (unsigned i=0;i<16u;++i) {
        gaw_sms_vdp_control_write((uint8_t)(seed+i));
        gaw_sms_vdp_control_write((uint8_t)(0x80u+i));
    }
    gaw_sms_vdp_control_write(0);
    gaw_sms_vdp_control_write(0xC0);
    for (unsigned i=0;i<32u;++i) gaw_sms_vdp_data_write((uint8_t)(seed+i));
    /* A half-written command must be cancelled by the status acknowledge. */
    gaw_sms_vdp_control_write(0xAB);
    gaw_host_set_pad((uint8_t)((seed*7u+3u)&63u));
    gaw_video_status_pending((uint8_t)((path?0x80u:0u)|status));
    gaw_host_clear_sound_trace();
}

static void compare(unsigned sound_count) {
    for (unsigned i=0;i<sizeof ram;++i) if(ram[i]!=gaw_ram[i]) {
        fprintf(stderr,"IRQ case%u RAM%04X ref%02X native%02X\n",case_now,0xC000u+i,ram[i],gaw_ram[i]);
        assert(0);
    }
    assert(memcmp(video,gaw_sms_vram(),sizeof video)==0);
    assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);
    assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
    assert(sound_count==gaw_host_sound_trace(actual_sound,256));
    assert(memcmp(sound,actual_sound,sound_count*sizeof *sound)==0);
    assert(gaw_video_status_read()==0);
    assert(gaw_host_frame_count()==0);
    assert(gaw_audio_faults()==0);
}

int main(void) {
    for(unsigned path=0;path<3u;++path)
    for(unsigned status=0;status<0x80u;status+=0x20u)
    for(unsigned mode=0;mode<2u;++mode)
    for(unsigned seed=0;seed<128u;++seed) {
        setup(path,status,seed,mode);
        assert(gaw_sms_compat_irq_call());
        assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);
        memcpy(video,gaw_sms_vram(),sizeof video);
        memcpy(cram,gaw_sms_cram(),sizeof cram);
        memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        unsigned count=gaw_host_sound_trace(sound,256);
        unsigned random=gaw_sms_compat_refresh_trace(entropy,64);
        assert(count<=256u&&random<=64u);
        setup(path,status,seed,mode);
        gaw_host_set_entropy_sequence(entropy,random);
        gaw_irq_service(gaw_platform_read_pad_sms_bits());
        compare(count);
        ++case_now;
    }
    for(unsigned counter=0;counter<256u;++counter) {
        gaw_ram_write8(0xC01Cu,(uint8_t)counter);
        assert(gaw_sms_compat_raw_call_args(0,0x0066,0,0,0,0));
        uint8_t expected=gaw_ram_read8(0xC01Cu);
        gaw_ram_write8(0xC01Cu,(uint8_t)counter);
        gaw_nmi_pause();
        assert(gaw_ram_read8(0xC01Cu)==expected);
    }
    printf("native full IRQ differential tests: OK (%u sync/async/line cases, 256 NMI cases)\n",case_now);
    return 0;
}
