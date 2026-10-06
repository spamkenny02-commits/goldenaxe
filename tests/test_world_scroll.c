#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_assets.h"
#include "gaw_core.h"
#include "gaw_entity.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_video.h"
#include "gaw_world.h"

static uint8_t ram[0x1F90],vram[0x4000],cram[32],regs[16];
static uint8_t frame_ram[40][0x1F90],frame_vram[40][0x4000],frame_cram[40][32],frame_regs[40][16];
static unsigned reference,observed,total,cell,direction,variant;
static void compare(const uint8_t *a,const uint8_t *b,unsigned n,const char *kind,unsigned base){
    for(unsigned i=0;i<n;++i)if(a[i]!=b[i]){
        fprintf(stderr,"scroll%03X dir%u variant%u frame%u %s%04X ref%02X native%02X\n",cell,direction,variant,observed,kind,base+i,a[i],b[i]);assert(0);
    }
}
static void observe(void){
    assert(observed<40u);
    if(reference){memcpy(frame_ram[observed],gaw_ram,sizeof ram);memcpy(frame_vram[observed],gaw_sms_vram(),sizeof vram);memcpy(frame_cram[observed],gaw_sms_cram(),32);memcpy(frame_regs[observed],gaw_sms_vdp_regs(),16);}
    else{assert(observed<total);compare(frame_ram[observed],gaw_ram,sizeof ram,"RAM",0xC000);compare(frame_vram[observed],gaw_sms_vram(),sizeof vram,"VRAM",0);compare(frame_cram[observed],gaw_sms_cram(),32,"CRAM",0);compare(frame_regs[observed],gaw_sms_vdp_regs(),16,"REG",0);}
    ++observed;
}
static void setup(void){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,GAW_RAM_SIZE);
    gaw_ram_write8(0xDE05,0x80);gaw_ram_write8(0xDE03,(uint8_t)(variant&1u?0x80u:0));
    gaw_ram_write16le(RAM_WORLD_CELL_ID,(uint16_t)cell);(void)gaw_world_load_current_cell();
    gaw_ram_write8(0xC066,(uint8_t)(15u-gaw_ram_read8(0xC040)));gaw_assets_restore_scene();gaw_world_expand_metatiles();
    for(unsigned i=0;i<0x4000u;++i)gaw_video_write_at((uint16_t)i,(uint8_t)(i*17u+variant));
    const uint8_t r[11]={0x06,0xE0,0x0E,0,0,0x7E,4,0,0,0,0x9F};
    for(unsigned i=0;i<11u;++i){gaw_sms_vdp_control_write(r[i]);gaw_sms_vdp_control_write((uint8_t)(0x80u+i));if(i<11u)gaw_ram_write8((uint16_t)(0xC010u+i),r[i]);}
    gaw_ram_write16le(0xC02C,0x0263);gaw_ram_write8(0xC01D,12);gaw_ram_write8(0xC02F,(uint8_t)(variant*73u));
    gaw_ram_write8(0xC0AD,1);gaw_ram_write8(0xC0AC,1);gaw_ram_write8(0xC06C,(uint8_t)(variant+1u));
    gaw_ram_write8(0xC047,(uint8_t)(variant*4u));
    GawEntity *p=gaw_entity(0);p->raw[ENT_TYPE]=2;p->raw[ENT_FLAGS]=0x41;p->raw[ENT_STATE]=1;
    gaw_entity_set16(p,ENT_ACCUM0,0x40A5);gaw_entity_set16(p,ENT_ACCUM1,0x88B7);
    if(direction==0u)p->raw[0x13]=0x0F;
    else if(direction==1u)p->raw[0x13]=0xF1;
    else if(direction==2u)p->raw[0x11]=0x0F;
    else if(direction==3u)p->raw[0x11]=0xA1;
    p->raw[ENT_DIRECTION]=(uint8_t)variant;gaw_ram_write16le(0xC308,0x80A0);
    gaw_entity_set16(p,ENT_DELTA0,0x1234);gaw_entity_set16(p,ENT_DELTA1,0xABCD);p->raw[ENT_MOTION_PHASE]=7;
    for(unsigned i=1;i<32u;++i){GawEntity *e=gaw_entity(i);e->raw[ENT_TYPE]=(uint8_t)((i&1u)?32:0);e->raw[ENT_FLAGS]=3;}
    gaw_host_queue_pad(3,0x10);gaw_host_queue_pad(8,0);gaw_host_queue_pause(12);gaw_host_set_frame_observer(observe);
}
static void guard_tests(void){
    const unsigned cells[]={0x77,0x95,0xFF,0x177};const uint8_t delta[]={0xFF,1,0xF0,0x10};unsigned cases=0;
    for(unsigned c=0;c<4u;++c)for(unsigned layer=0;layer<2u;++layer)for(unsigned d=0;d<4u;++d)for(unsigned stage=0;stage<5u;++stage)for(unsigned x=0;x<2u;++x){
        for(unsigned pass=0;pass<2u;++pass){
            gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,GAW_RAM_SIZE);
            gaw_ram_write16le(RAM_WORLD_CELL_ID,(uint16_t)cells[c]);gaw_ram_write8(0xC040,(uint8_t)layer);gaw_ram_write8(0xC06C,(uint8_t)stage);gaw_ram_write8(0xC311,(uint8_t)(x?0x70:0x50));
            for(unsigned i=0;i<8u;++i)gaw_ram_write8((uint16_t)(0xC600u+i*0x30u),(uint8_t)(i&1u));
            if(!pass){assert(gaw_sms_compat_raw_call_args(0,d<2u?0x21CBu:0x21C5u,0,0,0,delta[d]));memcpy(ram,gaw_ram,sizeof ram);}
            else{gaw_world_change_neighbor(delta[d],d<2u);compare(ram,gaw_ram,sizeof ram,"guard RAM",0xC000);}
        }
        ++cases;
    }
    printf("native world route differential tests: OK (%u cases)\n",cases);
}
int main(void){
    guard_tests();const unsigned cells[]={0x95,0x77,0x96,0xAA,0x0F,0,0xFF,0x101,0x1A2,0x1E7,0x1FF};unsigned cases=0;
    for(unsigned c=0;c<sizeof cells/sizeof cells[0];++c)for(direction=0;direction<5u;++direction)for(variant=0;variant<4u;++variant){
        cell=cells[c];reference=1;observed=0;setup();assert(gaw_sms_compat_raw_call_args(0,0x2051,0,0,0,0));assert(!gaw_sms_compat_faults());total=observed;
        memcpy(ram,gaw_ram,sizeof ram);memcpy(vram,gaw_sms_vram(),sizeof vram);memcpy(cram,gaw_sms_cram(),32);memcpy(regs,gaw_sms_vdp_regs(),16);
        reference=0;observed=0;setup();assert(gaw_world_check_boundary_transition()==(direction<4u));
        assert(observed==total&&gaw_host_frame_count()==total);compare(ram,gaw_ram,sizeof ram,"RAM",0xC000);compare(vram,gaw_sms_vram(),sizeof vram,"VRAM",0);compare(cram,gaw_sms_cram(),32,"CRAM",0);compare(regs,gaw_sms_vdp_regs(),16,"REG",0);++cases;
    }
    printf("native world scrolling differential tests: OK (%u complete cycles)\n",cases);return 0;
}
