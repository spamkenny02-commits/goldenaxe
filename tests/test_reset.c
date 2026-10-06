#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"

static uint8_t expected_sram[0x8000],expected_ram[GAW_RAM_SIZE];
static uint8_t expected_vram[0x4000],expected_cram[32],expected_regs[16];

static void seed_save(unsigned page,int bad_byte,uint8_t saved) {
    memset(gaw_ram,0xA5,sizeof gaw_ram);
    gaw_ram_write8(0xDFFC,(uint8_t)(page?4u:0u));
    gaw_sms_compat_reset();
    for(unsigned i=0;i<0x8000u;++i)
        gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*37u+13u));
    for(unsigned i=0;i<26u;++i)
        gaw_platform_sram_write((uint16_t)(page+0x10u+i),
                               gaw_sms_rom_bank_read(0u,(uint16_t)(0x03EAu+i)));
    gaw_platform_sram_write((uint16_t)(page+0x30u),saved);
    if(bad_byte>=0) {
        uint16_t a=(uint16_t)(page+0x10u+(unsigned)bad_byte);
        gaw_platform_sram_write(a,(uint8_t)(gaw_platform_sram_read(a)^0x80u));
    }
}

static void test_save(unsigned page,int bad_byte,uint8_t saved) {
    seed_save(page,bad_byte,saved);
    assert(gaw_sms_compat_call(0,0x0404));
    assert(gaw_sms_compat_faults()==0);
    memcpy(expected_ram,gaw_ram,sizeof expected_ram);
    for(unsigned i=0;i<sizeof expected_sram;++i)
        expected_sram[i]=gaw_platform_sram_read((uint16_t)i);
    seed_save(page,bad_byte,saved);
    gaw_save_initialize_native();
    for(unsigned i=0;i<sizeof expected_sram;++i)
        assert(expected_sram[i]==gaw_platform_sram_read((uint16_t)i));
    /* $DFF0 onward is the reference CPU's stack/mapper workspace. */
    assert(memcmp(expected_ram,gaw_ram,0x1FE0u)==0);
    assert(gaw_ram_read8(0xC036)==(bad_byte<0?saved:0xA5u));
    assert(gaw_platform_sram_read((uint16_t)(page+0x1FFFu))==
           (uint8_t)((page+0x1FFFu)*37u+13u));
}

static void seed_video(void) {
    memset(gaw_ram,0xA5,sizeof gaw_ram);
    gaw_sms_compat_reset();
    gaw_sms_vdp_control_write(0);gaw_sms_vdp_control_write(0x40);
    for(unsigned i=0;i<0x4000u;++i)gaw_sms_vdp_data_write((uint8_t)(i*17u+7u));
}

static void test_video(void) {
    seed_video();
    assert(gaw_sms_compat_call(0,0x03C0));
    memcpy(expected_ram,gaw_ram,sizeof expected_ram);
    memcpy(expected_vram,gaw_sms_vram(),sizeof expected_vram);
    memcpy(expected_cram,gaw_sms_cram(),sizeof expected_cram);
    memcpy(expected_regs,gaw_sms_vdp_regs(),sizeof expected_regs);
    seed_video();gaw_video_initialize_native();
    assert(memcmp(expected_ram,gaw_ram,0x1FE0u)==0);
    assert(memcmp(expected_vram,gaw_sms_vram(),sizeof expected_vram)==0);
    assert(memcmp(expected_cram,gaw_sms_cram(),sizeof expected_cram)==0);
    assert(memcmp(expected_regs,gaw_sms_vdp_regs(),sizeof expected_regs)==0);
    /* Verify the final VDP address/code, too, by observing a following write. */
    gaw_sms_vdp_data_write(0x6B);
    assert(gaw_sms_cram()[0x11]==0x6B);
}

int main(void) {
    gaw_platform_init();
    for(unsigned page=0;page<=0x4000u;page+=0x4000u) {
        for(int bad=-1;bad<26;++bad)test_save(page,bad,0x53);
        test_save(page,-1,0);test_save(page,-1,0xFF);
    }
    test_video();
    puts("native reset differential tests: OK (58 SRAM cases + VDP state)");
    return 0;
}
