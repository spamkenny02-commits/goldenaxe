#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_effects.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_host.h"
#include "gaw_platform.h"

static uint8_t ram[GAW_RAM_SIZE],vram[0x4000],cram[32],regs[16];
static void setup(unsigned x,unsigned y,unsigned state,unsigned count,unsigned slot){
    gaw_platform_init();gaw_sms_compat_reset();
    for(unsigned i=0;i<GAW_RAM_SIZE;++i)gaw_ram[i]=(uint8_t)(i*13u+5u);
    for(unsigned i=0;i<0x100u;++i)gaw_ram_write8((uint16_t)(0xDC00u+i),(uint8_t)(i%32u));
    gaw_ram_write8(0xC09A,(uint8_t)y);gaw_ram_write8(0xC09B,(uint8_t)x);
    gaw_ram_write8((uint16_t)(0xC090u+slot*8u),(uint8_t)state);
    gaw_ram_write8((uint16_t)(0xC091u+slot*8u),(uint8_t)count);
}
int main(void){
    unsigned cases=0;
    const unsigned counts[]={0,1,2,255};
    for(unsigned slot=0;slot<2u;++slot)for(unsigned state=3;state<=4;++state)
    for(unsigned x=0;x<256u;x+=16u)for(unsigned y=0;y<256u;y+=8u)
    for(unsigned c=0;c<4u;++c){
        uint16_t a=(uint16_t)(0xC090u+slot*8u);
        setup(x,y,state,counts[c],slot);
        assert(gaw_sms_compat_indexed_call(1,state==3u?0x6D2Cu:0x6D40u,a));
        assert(gaw_sms_compat_faults()==0);
        memcpy(ram,gaw_ram,sizeof ram);memcpy(vram,gaw_sms_vram(),sizeof vram);
        memcpy(cram,gaw_sms_cram(),sizeof cram);memcpy(regs,gaw_sms_vdp_regs(),sizeof regs);
        setup(x,y,state,counts[c],slot);assert(gaw_effect_native_step(a));
        /* Exclude the original CPU's temporary stack area. */
        assert(memcmp(ram,gaw_ram,0x1F80u)==0);
        assert(memcmp(vram,gaw_sms_vram(),sizeof vram)==0);
        assert(memcmp(cram,gaw_sms_cram(),sizeof cram)==0);
        assert(memcmp(regs,gaw_sms_vdp_regs(),sizeof regs)==0);
        assert(gaw_host_frame_count()==0);++cases;
    }
    setup(0,0,0,0,0);assert(gaw_effect_native_step(0xC090));
    gaw_ram_write8(0xC090,5);assert(!gaw_effect_native_step(0xC090));
    printf("native effect cursor differential tests: OK (%u cases)\n",cases);
    return 0;
}
