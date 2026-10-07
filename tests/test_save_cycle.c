/* Complete production save -> SRAM-only reboot -> continue cycles.
   Service arrival is controlled; its menus are driven by pad input. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_video.h"
static uint8_t snapshot[0x8000], payload[0x250];
static void drive(void){
    assert(gaw_host_frame_count()<4000u);
    gaw_host_set_pad((uint8_t)(gaw_host_frame_count()%4u==0u?0x20:0));
}
static void new_game(void){
    gaw_reset();gaw_host_set_frame_observer(drive);
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x12);
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==4);
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x0C);
}
int main(void){
    unsigned cycles=0;
    for(unsigned page=0;page<=0x4000u;page+=0x4000u){
        for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,0xFF);
        new_game();
        gaw_ram_write8(0xDFFCu,(uint8_t)(page?4:0));gaw_save_initialize_native();
        for(unsigned pass=0;pass<2u;++pass)for(unsigned slot=0;slot<3u;++slot){
            gaw_ram_write8(0xC036u,(uint8_t)(slot+1u));
            gaw_ram_write8(0xC0B0u,(uint8_t)('A'+slot+pass*3u));
            gaw_ram_write8(0xC0DDu,(uint8_t)(17u+slot+pass*30u));
            gaw_ram_write8(0xC318u,(uint8_t)(12u+slot+pass*3u));
            gaw_ram_write16le(0xC0BBu,0x95);
            gaw_ram_write8(0xC0A7u,0);gaw_ram_write8(RAM_MAIN_STATE,0x16);
            for(unsigned i=0;i<0x8000u;++i)snapshot[i]=gaw_platform_sram_read((uint16_t)i);
            gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x0C);
            unsigned at=page+0x400u*(slot+1u);
            for(unsigned i=0;i<0x8000u;++i)
                /* Scene restoration also uses SRAM $1000-$149F as scratch. */
                if(i!=page+0x30u&&(i<page+0x1000u||i>=page+0x14A0u)&&(i<at||i>=at+sizeof payload))
                    assert(gaw_platform_sram_read((uint16_t)i)==snapshot[i]);
            assert(gaw_platform_sram_read((uint16_t)(page+0x30u))==slot+1u);
            for(unsigned i=0;i<sizeof payload;++i)payload[i]=gaw_platform_sram_read((uint16_t)(at+i));
            assert(payload[0]=='A'+slot+pass*3u);assert(payload[0x29]==12u+slot+pass*3u);assert(payload[0x2D]==17u+slot+pass*30u);
            assert(payload[0x12]==0x95&&payload[0x13]==0);
            for(unsigned i=0;i<0x8000u;++i)snapshot[i]=gaw_platform_sram_read((uint16_t)i);
            /* Work RAM, audio, video, pad, frame observer all reset; only SRAM survives. */
            gaw_reset();gaw_ram_write8(0xDFFCu,(uint8_t)(page?4:0));gaw_save_initialize_native();
            assert(gaw_ram_read8(0xC036u)==slot+1u);
            gaw_host_set_frame_observer(drive);gaw_dispatch_state_once();
            assert(gaw_ram_read8(RAM_MAIN_STATE)==6);
            payload[0x10]=payload[0x12];payload[0x11]=payload[0x13];
            assert(memcmp(gaw_ram_ptr(0xC0B0u),payload,sizeof payload)==0);
            assert(gaw_ram_read8(0xC318u)==12u+slot+pass*3u);
            for(unsigned i=0;i<0x8000u;++i)assert(gaw_platform_sram_read((uint16_t)i)==snapshot[i]);
            gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x0C);
            for(unsigned i=0;i<12u;++i)gaw_dispatch_state_once();
            assert(gaw_ram_read16le(RAM_WORLD_CELL_ID)==0x95);
            assert(gaw_ram_read8(0xC0DDu)==17u+slot+pass*30u);assert(gaw_ram_read8(0xC318u)==12u+slot+pass*3u);
            ++cycles;
        }
    }
    printf("native save/reboot/continue integration: OK (%u cycles, 3 slots x 2 SRAM pages x initial/overwrite, no interpreter)\n",cycles);
    return 0;
}
