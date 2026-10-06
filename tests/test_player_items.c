#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_player.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_video.h"
#include "gaw_world.h"

static uint8_t ram[0x1F90],video[0x4000],cram[32],regs[16],sram[0x8000];
static uint8_t frame_ram[256][0x1F90],frame_video[256][0x4000],frame_cram[256][32],frame_regs[256][16];
static unsigned reference,observed,total,current_item,current_case;
static void compare(const uint8_t *expected,const uint8_t *actual,unsigned count,const char *kind,unsigned base){
    for(unsigned i=0;i<count;++i)if(expected[i]!=actual[i]){
        fprintf(stderr,"item%u case%u frame%u %s%04X ref%02X native%02X\n",current_item,current_case,observed,kind,base+i,expected[i],actual[i]);assert(0);
    }
}
static void observe(void){
    assert(observed<256u);
    if(reference){memcpy(frame_ram[observed],gaw_ram,sizeof ram);memcpy(frame_video[observed],gaw_sms_vram(),sizeof video);memcpy(frame_cram[observed],gaw_sms_cram(),32);memcpy(frame_regs[observed],gaw_sms_vdp_regs(),16);}
    else{assert(observed<total);compare(frame_ram[observed],gaw_ram,sizeof ram,"RAM",0xC000);compare(frame_video[observed],gaw_sms_vram(),sizeof video,"VRAM",0);compare(frame_cram[observed],gaw_sms_cram(),32,"CRAM",0);compare(frame_regs[observed],gaw_sms_vdp_regs(),16,"REG",0);}
    ++observed;
}
static void setup(unsigned item,unsigned variant){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,GAW_RAM_SIZE);
    gaw_ram_write8(0xDE05u,0x80);gaw_ram_write16le(0xC034u,0xDD00);
    gaw_ram_write8(0xDFFCu,(uint8_t)((variant&1u)*4u));
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*11u+variant));
    uint16_t cell=(uint16_t)(item==3u?0x101u:variant&2u?0x96u:0x95u);
    gaw_ram_write16le(RAM_WORLD_CELL_ID,cell);(void)gaw_world_load_current_cell();
    gaw_ram_write8(0xC066u,(uint8_t)(15u-gaw_ram_read8(0xC040u)));
    gaw_assets_restore_scene();gaw_world_expand_metatiles();
    gaw_ram_write8(0xC010u,0x16);gaw_ram_write8(0xC011u,0xE0);
    for(unsigned i=0;i<2u;++i){gaw_sms_vdp_control_write(gaw_ram_read8(0xC010u+i));gaw_sms_vdp_control_write((uint8_t)(0x80u+i));}
    gaw_sms_vdp_control_write(14);gaw_sms_vdp_control_write(0x82);
    gaw_sms_vdp_control_write(0x7E);gaw_sms_vdp_control_write(0x85);
    gaw_ram_write8(0xC0DFu,(uint8_t)item);gaw_ram_write8(0xC0DAu,24);gaw_ram_write8(0xC0DCu,24);gaw_ram_write8(0xC318u,(uint8_t)(variant&2u?24:16));
    gaw_ram_write8(0xC300u,2);gaw_ram_write8(0xC301u,1);gaw_ram_write8(0xC303u,1);
    gaw_ram_write8(0xC311u,0x58);gaw_ram_write8(0xC313u,0x88);
    gaw_ram_write16le(0xC308u,0x80A0);gaw_ram_write8(0xC0E0u,1);gaw_ram_write8(0xC0E1u,1);gaw_ram_write8(0xC0F5u,(uint8_t)(variant&1u));
    gaw_ram_write8(0xC0E8u,1);gaw_ram_write8(0xC0E9u,1);gaw_ram_write16le(0xC0C2u,(uint16_t)(variant&2u?0x101u:0xAAu));
    gaw_ram_write8(0xC01Du,12);gaw_ram_write8(0xC02Fu,(uint8_t)(variant*17u));
    if(item==3u){gaw_ram_write8(0xC072u,(uint8_t)(variant&4u?0:1));gaw_ram_write8(0xC0ADu,(uint8_t)(variant&2u));}
    if(item==10u){
        gaw_ram_write8(0xC0ACu,(uint8_t)(variant&1u));if(!(variant&2u))gaw_ram_write8(0xDC34u,0x3F);
        for(unsigned i=16;i<32u;++i){GawEntity *e=gaw_entity(i);e->raw[ENT_TYPE]=(uint8_t)(i&2u?0:32);e->raw[ENT_FLAGS]=(uint8_t)(i&1u);e->raw[ENT_STATE]=4;e->raw[ENT_COOLDOWN]=9;}
    }
    if(item==12u){
        gaw_ram_write8(0xC0DDu,(uint8_t)(variant*19u));gaw_ram_write8(0xC30Au,(uint8_t)(variant&3u));
        if(variant<4u)gaw_ram_write8(0xC052u,(uint8_t)(0xB5u+variant));
        else if(variant<6u)gaw_ram_write8(0xC054u,(uint8_t)(variant==4u?0xB5u:0xB7u));
        else if(variant==6u)gaw_ram_write8(0xC313u,0x89);
        else gaw_ram_write8(0xC040u,1);
    }
    if(item!=12u&&item!=3u&&(variant&4u))gaw_ram_write8(0xC040u,1);
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*7u+variant));
    /* Keep the staging SAT valid, and leave varied source/destination patterns. */
    gaw_ram_write8(0xDD40u,0xD0);unsigned confirm=(item==11u&&(variant&1u))?25u:9u;
    gaw_host_queue_pad(confirm,0x20);gaw_host_queue_pad(confirm+1u,0);
    gaw_host_set_frame_observer(observe);
}
int main(void){
    const unsigned items[]={3,8,9,10,11,12};const uint16_t targets[]={0x2FD2,0x30D6,0x30E8,0x3124,0x31E7,0x2F18};unsigned cases=0;
    for(unsigned kind=0;kind<6u;++kind)for(unsigned variant=0;variant<8u;++variant){
        current_item=items[kind];current_case=variant;reference=1;observed=0;setup(current_item,variant);
        if(!gaw_sms_compat_raw_indexed_call(0,targets[kind],0xC300)){
            fprintf(stderr,"reference item%u case%u fault%04X frames%u\n",current_item,current_case,gaw_sms_compat_last_pc(),observed);assert(0);
        }
        assert(!gaw_sms_compat_faults());total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),32);memcpy(regs,gaw_sms_vdp_regs(),16);
        for(unsigned i=0;i<0x8000u;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        reference=0;observed=0;setup(current_item,variant);
        if(kind==5u)gaw_player_grid_transition(gaw_entity(0));else gaw_player_use_item(gaw_entity(0));
        assert(observed==total&&gaw_host_frame_count()==total);
        compare(ram,gaw_ram,sizeof ram,"RAM",0xC000);compare(video,gaw_sms_vram(),sizeof video,"VRAM",0);
        compare(cram,gaw_sms_cram(),32,"CRAM",0);compare(regs,gaw_sms_vdp_regs(),16,"REG",0);
        for(unsigned i=0;i<0x8000u;++i)assert(sram[i]==gaw_platform_sram_read((uint16_t)i));
        ++cases;
    }
    printf("native player item differential tests: OK (%u complete cycles)\n",cases);return 0;
}
