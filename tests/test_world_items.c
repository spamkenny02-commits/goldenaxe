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
static uint8_t frame_ram[512][0x1F90],frame_video[512][0x4000],frame_cram[512][32],frame_regs[512][16];
static unsigned reference,observed,total,current_item,current_case;
static void compare(const uint8_t *expected,const uint8_t *actual,unsigned count,const char *kind,unsigned base){
    for(unsigned i=0;i<count;++i)if(expected[i]!=actual[i]){
        fprintf(stderr,"item%u case%u frame%u %s%04X ref%02X native%02X\n",current_item,current_case,observed,kind,base+i,expected[i],actual[i]);assert(0);
    }
}
static void observe(void){
    assert(observed<512u);
    if(reference){memcpy(frame_ram[observed],gaw_ram,sizeof ram);memcpy(frame_video[observed],gaw_sms_vram(),sizeof video);memcpy(frame_cram[observed],gaw_sms_cram(),32);memcpy(frame_regs[observed],gaw_sms_vdp_regs(),16);}
    else{assert(observed<total);compare(frame_ram[observed],gaw_ram,sizeof ram,"RAM",0xC000);compare(frame_video[observed],gaw_sms_vram(),sizeof video,"VRAM",0);compare(frame_cram[observed],gaw_sms_cram(),32,"CRAM",0);compare(frame_regs[observed],gaw_sms_vdp_regs(),16,"REG",0);}
    ++observed;
}
typedef struct {uint16_t callback,position,flag;uint8_t cell,value;} ItemCase;
static const ItemCase items[]={
 {0xB3DD,0x01DC,0xC0E3,0x10,1},{0xB3E4,0x01D8,0xC0EA,0x12,1},
 {0xB419,0x01C4,0xC0E1,0x1D,2},{0xB4ED,0x02E4,0xC0EE,0x57,1},
 {0xB5C4,0x0248,0xC0EB,0x9B,1},{0xB5D7,0x01CC,0xC0EC,0xA2,1},
 {0xB613,0x0358,0xC0EF,0xA9,1},{0xB64F,0x0264,0xC0E1,0xB6,1},
 {0xB6C2,0x02C4,0xC0F0,0xD5,1},{0xB751,0x0370,0xC0ED,0xF4,1},
 {0xB205,0x025C,0xC0DC,0xAF,32},{0xB205,0x025C,0xC0DA,0xAF,32}
};
static void setup(const ItemCase *item,unsigned variant){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,GAW_RAM_SIZE);
    gaw_ram_write8(0xDE05,0x80);gaw_ram_write16le(0xC034,0xDD00);
    gaw_ram_write8(0xDFFC,(uint8_t)((variant&1u)*4u));
    for(unsigned i=0;i<0x8000u;++i)gaw_platform_sram_write((uint16_t)i,(uint8_t)(i*11u+variant));
    gaw_ram_write16le(RAM_WORLD_CELL_ID,(uint16_t)(item->callback==0xB205u?item->cell:0x100u|item->cell));
    (void)gaw_world_load_current_cell();gaw_ram_write8(0xC066,(uint8_t)(15u-gaw_ram_read8(0xC040)));gaw_assets_restore_scene();gaw_world_expand_metatiles();
    gaw_ram_write8(0xC010,0x16);gaw_ram_write8(0xC011,0xE0);
    for(unsigned i=0;i<2;++i){gaw_sms_vdp_control_write(gaw_ram_read8(0xC010u+i));gaw_sms_vdp_control_write((uint8_t)(0x80u+i));}
    gaw_sms_vdp_control_write(14);gaw_sms_vdp_control_write(0x82);gaw_sms_vdp_control_write(0x7E);gaw_sms_vdp_control_write(0x85);
    gaw_ram_write8(0xC0DF,0);gaw_ram_write8(0xC0DA,24);gaw_ram_write8(0xC0DC,24);gaw_ram_write8(0xC318,16);
    gaw_ram_write8(0xC300,2);gaw_ram_write8(0xC301,1);gaw_ram_write8(0xC303,1);gaw_ram_write8(0xC311,0x58);gaw_ram_write8(0xC313,0x88);
    gaw_ram_write16le(0xC308,0x80A0);gaw_ram_write8(0xC0E0,1);gaw_ram_write8(0xC0F1,1);gaw_ram_write8(0xC0F2,1);
    gaw_ram_write8(0xC01D,12);gaw_ram_write8(0xC02F,(uint8_t)(variant*17u));
    gaw_ram_write8(0xC0A6,(uint8_t)(variant==2u?0:0x14));gaw_ram_write16le(0xC060,item->position);
    if(variant==1u)gaw_ram_write8((uint16_t)(0xC100u+item->cell),4);
    if(item->callback==0xB205u){
        uint8_t from=(uint8_t)(item->flag==0xC0DCu?0x32u:0x18u);gaw_ram_write16le(0xC0BB,from);
        gaw_ram_write8(0xC0A6,(uint8_t)(variant==2u?0x14u:variant==3u?0u:0x30u));
        if(variant==1u)gaw_ram_write8((uint16_t)(0xC100u+from),2);
    }
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*7u+variant));
    gaw_ram_write8(0xDD40,0xD0);gaw_host_queue_pad(210,0x20);gaw_host_queue_pad(211,0);
    if(item->callback==0xB205u){gaw_host_queue_pad(430,0x20);gaw_host_queue_pad(431,0);}
    gaw_host_set_frame_observer(observe);
}
int main(void){
    unsigned cases=0;
    for(unsigned index=0;index<sizeof items/sizeof items[0];++index)for(unsigned variant=0;variant<(items[index].callback==0xB205u?4u:3u);++variant){
        const ItemCase *item=&items[index];current_item=index;current_case=variant;
        reference=1;observed=0;setup(item,variant);
        assert(gaw_sms_compat_raw_call_args(2,item->callback,0,0,0,0));assert(!gaw_sms_compat_faults());total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(video,gaw_sms_vram(),sizeof video);memcpy(cram,gaw_sms_cram(),32);memcpy(regs,gaw_sms_vdp_regs(),16);
        for(unsigned i=0;i<0x8000u;++i)sram[i]=gaw_platform_sram_read((uint16_t)i);
        reference=0;observed=0;setup(item,variant);assert(gaw_world_native_callback(item->callback));
        if(observed!=total||gaw_host_frame_count()!=total)fprintf(stderr,"item%u variant%u frames ref%u native%u host%u\n",index,variant,total,observed,gaw_host_frame_count());
        assert(observed==total&&gaw_host_frame_count()==total);
        compare(ram,gaw_ram,sizeof ram,"RAM",0xC000);compare(video,gaw_sms_vram(),sizeof video,"VRAM",0);
        compare(cram,gaw_sms_cram(),32,"CRAM",0);compare(regs,gaw_sms_vdp_regs(),16,"REG",0);
        for(unsigned i=0;i<0x8000u;++i)assert(sram[i]==gaw_platform_sram_read((uint16_t)i));
        if(variant==0u)assert(gaw_ram_read8(item->flag)==item->value);
        ++cases;
    }
    printf("native world item differential tests: OK (%u pickup/persistence/inactive cases)\n",cases);return 0;
}
