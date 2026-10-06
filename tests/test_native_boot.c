#include <assert.h>
#include <stdio.h>
#include "gaw_core.h"
#include "gaw_audio.h"
#include "gaw_host.h"
#include "gaw_ram.h"
#include "gaw_video.h"

static void drive_new_game(void){
    assert(gaw_host_frame_count()<2000u);
    assert(gaw_audio_faults()==0);
    uint8_t state=gaw_ram_read8(RAM_MAIN_STATE);
    gaw_host_set_pad((uint8_t)(state!=0x0Cu&&gaw_host_frame_count()%4u==0u?0x20:0));
}
int main(void){
    gaw_reset();gaw_host_set_frame_observer(drive_new_game);
    assert(gaw_ram_read8(RAM_MAIN_STATE)==0);
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x12);
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==4);
    for(unsigned i=0;i<8u;++i)assert(gaw_ram_read8((uint16_t)(0xC0B0u+i))=='A');
    gaw_dispatch_state_once();assert(gaw_ram_read8(RAM_MAIN_STATE)==0x0C);
    assert(gaw_ram_read16le(RAM_WORLD_CELL_ID)==0x95);
    assert(gaw_ram_read8(0xC318u)==24);
    unsigned start=gaw_host_frame_count();
    for(unsigned i=0;i<24u;++i)gaw_dispatch_state_once();
    assert(gaw_host_frame_count()==start+24u);
    assert(gaw_ram_read8(RAM_MAIN_STATE)==0x0C);
    assert(gaw_sms_vdp_regs()[1]&0x40u);
    assert(gaw_host_sound_trace(0,0)>100u);
    puts("native boot/new-game integration: OK (no instruction interpreter linked)");return 0;
}
