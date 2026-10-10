#include <assert.h>
#include <stdio.h>
#include "gaw_video.h"
static void address(unsigned a){gaw_sms_vdp_control_write((uint8_t)a);gaw_sms_vdp_control_write((uint8_t)(a>>8));}
int main(void){
    gaw_video_reset();assert(gaw_sms_take_name_dirty());assert(!gaw_sms_take_name_dirty());
    assert(gaw_sms_take_sat_dirty());assert(!gaw_sms_take_sat_dirty());
    for(unsigned i=0;i<512u;++i){assert(gaw_sms_take_tile_dirty(i));assert(!gaw_sms_take_tile_dirty(i));}
    address(0x7FFF);gaw_sms_vdp_data_write(0xA5);gaw_sms_vdp_data_write(0x42);
    assert(gaw_sms_vram()[0x3FFF]==0xA5&&gaw_sms_vram()[0]==0x42);
    assert(gaw_sms_take_tile_dirty(511)&&gaw_sms_take_tile_dirty(0));
    address(0x3FFF);assert(gaw_sms_vdp_data_read()==0xA5);assert(gaw_sms_vdp_data_read()==0x42);
    address(0xC01F);gaw_sms_vdp_data_write(0x3F);gaw_sms_vdp_data_write(0x12);
    assert(gaw_sms_cram()[31]==0x3F&&gaw_sms_cram()[0]==0x12);
    gaw_sms_vdp_control_write(0x0E);gaw_sms_vdp_control_write(0x82);
    assert(gaw_sms_vdp_regs()[2]==0x0E&&gaw_sms_take_name_dirty());
    address(0x7800);gaw_sms_vdp_data_write(0x31);
    address(0x7EFA);gaw_sms_vdp_data_write(0x75);
    assert(gaw_sms_take_name_rows_dirty()==((uint32_t)1u|((uint32_t)1u<<27)));
    address(0x7800);gaw_sms_vdp_data_write(0x31);
    assert(!gaw_sms_take_name_rows_dirty());
    gaw_sms_vdp_control_write(0x0E);gaw_sms_vdp_control_write(0x82);
    assert(!gaw_sms_take_name_rows_dirty()); /* Unchanged base does not rebuild. */
    gaw_sms_vdp_control_write(0x0C);gaw_sms_vdp_control_write(0x82);
    assert(gaw_sms_take_name_rows_dirty()==0x0FFFFFFFu);
    gaw_sms_vdp_control_write(0x0E);gaw_sms_vdp_control_write(0x82);
    assert(gaw_sms_take_name_rows_dirty()==0x0FFFFFFFu);
    assert(!gaw_sms_take_name_dirty());
    gaw_sms_vdp_control_write(4);gaw_sms_vdp_control_write(0x80);
    assert(gaw_sms_take_sat_dirty());
    gaw_sms_vdp_control_write(4);gaw_sms_vdp_control_write(0x80);
    assert(!gaw_sms_take_sat_dirty());
    gaw_sms_vdp_control_write(5);gaw_sms_vdp_control_write(0x80);
    assert(gaw_sms_take_sat_dirty());
    gaw_video_vblank_pending();assert(gaw_video_status_read()==0x80);assert(gaw_video_status_read()==0);
    gaw_sms_vdp_control_write(0x99);(void)gaw_video_status_read();
    address(0x4010);gaw_sms_vdp_data_write(0x77);assert(gaw_sms_vram()[0x10]==0x77);
    address(0x0010);assert(gaw_sms_vdp_data_read()==0x77);gaw_video_reset();
    assert(gaw_sms_vdp_data_read()==0);assert(gaw_video_status_read()==0);
    assert(gaw_sms_rom_bank_read(0,0)==gaw_sms_rom_bank_read(16,0x4000));
    puts("standalone video/data tests: OK (no instruction interpreter linked)");return 0;
}
