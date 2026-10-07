#include "include/gaw_assets.h"
#include "include/gaw_core.h"
#include "include/gaw_platform.h"
#include "include/gaw_player.h"
#include "include/gaw_ram.h"
#include "include/gaw_ui.h"
#include "include/gaw_video.h"
#include "include/gaw_world.h"

#define R(a) gaw_ram_read8((uint16_t)(a))
#define W(a,v) gaw_ram_write8((uint16_t)(a),(uint8_t)(v))
#define R16(a) gaw_ram_read16le((uint16_t)(a))
#define W16(a,v) gaw_ram_write16le((uint16_t)(a),(uint16_t)(v))
static uint8_t rom(uint16_t a){return gaw_sms_rom_bank_read(2,a);}
static void address(uint16_t a){gaw_platform_video_command(a);}

/* Bank 2 $837C: 15x10 tiles, each containing an 8x8 part of the map. */
static void map_setup(void){
    for(unsigned i=0;i<4u;++i)W(0xDCACu+i,rom(0x83E8u+i));
    gaw_ui_box(0xD60Eu,19,13);
    address(0x4000u);for(unsigned i=0;i<0x1400u;++i)gaw_sms_vdp_data_write(0);
    for(unsigned column=0;column<15u;++column){
        address((uint16_t)(0x520Cu+column*32u));
        for(unsigned remaining=20u;remaining;--remaining)gaw_sms_vdp_data_write((remaining&3u)?0:0xFF);
    }
    uint16_t tile=0;
    for(unsigned row=0;row<10u;++row){
        for(unsigned col=0;col<15u;++col)W16(0xD692u+row*64u+col*2u,tile++);
        ++tile;
    }
    for(unsigned i=0;i<640u;++i)W(0xD601u+i*2u,R(0xD601u+i*2u)&~0x10u);
    gaw_wait_frame();gaw_ui_upload_name_table();
}

/* Bank 2 $844D: choose the strongest terrain class in a 2x2 cell area and
   OR its four color planes into one overview pixel. */
static void map_pixel(unsigned x,unsigned y){
    unsigned offset=y*32u+x*2u;
    uint8_t color=0;
    const unsigned delta[4]={0,1,16,17};
    for(unsigned i=0;i<4u;++i){
        uint8_t tile=R(0xDC00u+offset+delta[i]),packed=rom(0x84DEu+(tile>>1));
        uint8_t value=(uint8_t)((tile&1u)?packed&15u:packed>>4);
        if(value>color)color=value;
    }
    for(unsigned plane=0;plane<4u;++plane)W(0xDCC0u+plane,(color&(1u<<plane))?0x80u>>x:0);
    uint8_t cell=R(0xC0B9u);
    unsigned scanline=((uint8_t)(cell-0x10u)>>4)*5u+y;
    uint16_t at=(uint16_t)((scanline>>3)*512u+(cell&15u)*32u+(scanline&7u)*4u);
    for(unsigned plane=0;plane<4u;++plane){
        address((uint16_t)(at+plane));
        uint8_t value=(uint8_t)(gaw_sms_vdp_data_read()|R(0xDCC0u+plane));
        address((uint16_t)(0x4000u+at+plane));gaw_sms_vdp_data_write(value);
    }
}

/* Bank 2 $83EC: blink Arthur's position or the acquired map symbol. */
static void map_marker(void){
    uint16_t descriptor;
    if(!(R(RAM_FRAME_COUNTER)&0x10u)){
        if(!R(0xC0F5u))return;
        W(0xD113u,0x90);W(0xD111u,0x30);descriptor=0x8449u;
    }else{
        uint8_t cell=R(0xC0B9u);
        W(0xD113u,(cell&15u)*8u+(R(0xC313u)>>5)+0x48u);
        uint8_t row=(uint8_t)((cell-0x10u)&0xF0u),position=(uint8_t)(R(0xC311u)-0x10u);
        W(0xD111u,(row>>2)+(row>>4)+(position>>5)+0x10u);descriptor=0x8445u;
    }
    gaw_ui_sprite(2,descriptor,0xD100u);
}

/* $31E7-$3291: overview generation, SRAM preservation, modal controls and
   complete restoration. All rendering targets the portable SMS shadow. */
void gaw_player_show_world_map(void){
    if(R(0xC040u))return;
    gaw_ui_clear_playfield();map_setup();
    (void)gaw_assets_unpack_tiles(5,0xBD71u,0x7F40u);
    uint16_t cell=R16(RAM_WORLD_CELL_ID),page=(R(0xDFFCu)&4u)?0x4000u:0u;
    W(0xDFFCu,R(0xDFFCu)|8u);
    for(unsigned i=0;i<160u;++i)gaw_platform_sram_write((uint16_t)(page+0x1400u+i),R(0xDC00u+i));
    W(0xDFFCu,R(0xDFFCu)&~8u);
    for(unsigned row=1;row<16u;++row)for(unsigned column=0;column<15u;++column){
        W16(RAM_WORLD_CELL_ID,row*16u+column);(void)gaw_world_load_current_cell();
        for(unsigned y=0;y<5u;++y)for(unsigned x=0;x<8u;++x)map_pixel(x,y);
    }
    W16(RAM_WORLD_CELL_ID,cell);
    W(0xDFFCu,R(0xDFFCu)|8u);
    for(unsigned i=0;i<160u;++i)W(0xDC00u+i,gaw_platform_sram_read((uint16_t)(page+0x1400u+i)));
    W(0xDFFCu,R(0xDFFCu)&~8u);W(0xDCBFu,3);
    do{
        gaw_wait_frame();W16(0xC024u,0xDD40);W16(0xC026u,0xDD80);
        map_marker();W(R16(0xC024u),0xD0);
    }while(!(R(RAM_INPUT_PRESSED)&0x30u));
    gaw_ui_clear_playfield();W(0xC0DFu,0);gaw_assets_update_inventory();
    gaw_assets_restore_scene();gaw_world_rebuild_display_native();
}
