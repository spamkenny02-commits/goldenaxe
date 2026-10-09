/* Magic projectiles, real boss phase tables and complete boss death sequences
   compared with unaccelerated original Z80 and replayed refresh samples. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_host.h"
#include "gaw_tables.h"
#include "gaw_entity.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
static uint8_t initial[GAW_RAM_SIZE], expected[0x1FE0];
static unsigned cases;
static void setup(void){
    gaw_platform_init();gaw_sms_compat_reset();memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write8(0xDE05,0x80);
}
static void compare(unsigned slot,uint16_t target,void (*native)(GawEntity *)){
    memcpy(initial,gaw_ram,sizeof initial);
    assert(gaw_sms_compat_raw_indexed_call((uint8_t)(target>=0x4000u?1:0),target,gaw_entity_addr(gaw_entity(slot))));
    assert(gaw_sms_compat_faults()==0);
    memcpy(expected,gaw_ram,sizeof expected);
    uint8_t entropy[64];unsigned count=gaw_sms_compat_refresh_trace(entropy,64);assert(count<=64);
    memcpy(gaw_ram,initial,sizeof initial);gaw_host_set_entropy_sequence(entropy,count);native(gaw_entity(slot));
    for(unsigned i=0;i<sizeof expected;++i)if(gaw_ram[i]!=expected[i]){
        fprintf(stderr,"magic/boss case%u routine%04X slot%u RAM%04X original%02X native%02X\n",cases,target,slot,0xC000u+i,expected[i],gaw_ram[i]);
        for(unsigned j=0x600;j<0x630;++j)if(gaw_ram[j]!=expected[j])fprintf(stderr,"  %04X original%02X native%02X\n",0xC000+j,expected[j],gaw_ram[j]);
        assert(0);
    }
    ++cases;
}
static void handler(GawEntity *e){assert(gaw_entity_native_handler(e,e->raw[ENT_TYPE]));}
int main(void){
    /* Boss identities come from map_entity_stats flags bit 6, not handler names. */
    const uint8_t max_state[]={10,10,8,2,18,18,18,14,14,18,18};
    const uint8_t counters[]={0,1,2,255};
    for(unsigned type=99;type<=109;++type)
    for(unsigned state=0;state<=max_state[type-99];state+=2)
    for(unsigned variant=0;variant<64;++variant){
        if(type==103 && state>=16)continue; /* Parts are exercised separately below. */
        setup();GawEntity *e=gaw_entity(16);
        e->raw[ENT_TYPE]=(uint8_t)type;e->raw[ENT_STATE]=(uint8_t)state;e->raw[ENT_FLAGS]=0x40;
        e->raw[ENT_HP]=90;e->raw[ENT_DIRECTION]=(uint8_t)(variant&(type<=100?1:3));
        e->raw[ENT_MOTION_PHASE]=(uint8_t)((variant&4)?1:0);
        e->raw[ENT_ANIM_FRAME]=(uint8_t)((variant&8)?(type>=106?6:2):0);
        e->raw[ENT_HIT_FLASH_TIMER]=(uint8_t)((variant&16)?1:0);
        for(unsigned off=0x20;off<0x30;++off)e->raw[off]=counters[variant&3];
        e->raw[0x20]&=7;e->raw[0x22]&=7;if(type==103)e->raw[0x21]=(uint8_t)(variant%3);e->raw[0x28]=(uint8_t)((variant&8)?31:16);
        e->raw[0x11]=(uint8_t)((variant&16)?0x30:0x50);e->raw[0x13]=(uint8_t)((variant&8)?0xD0:0x80);
        for(unsigned i=24;i<32;++i)gaw_entity(i)->raw[ENT_TYPE]=(uint8_t)((variant&32)?102:0);
        gaw_ram_write8(0xC311,(uint8_t)((variant&1)?0x80:0x30));gaw_ram_write8(0xC313,(uint8_t)((variant&2)?0xA0:0x30));
        gaw_ram_write8(0xC0DF,(uint8_t)((variant&8)?1:4));gaw_ram_write8(0xC0E1,(uint8_t)((variant&16)?2:1));
        e->raw[ENT_PENDING_DAMAGE]=(uint8_t)((variant&4)?2:0);
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)(variant*47));
        gaw_sms_compat_set_refresh_seed((uint8_t)variant);
        compare(16,gaw_entity_handler_targets[type],handler);
    }
    for(unsigned slot=17;slot<=21;++slot)for(unsigned state=16;state<=22;state+=2)
    for(unsigned variant=0;variant<24;++variant){
        setup();GawEntity *e=gaw_entity(slot);e->raw[ENT_TYPE]=103;e->raw[ENT_STATE]=(uint8_t)state;
        e->raw[ENT_FLAGS]=0x43;e->raw[ENT_HP]=60;e->raw[ENT_MOTION_PHASE]=(uint8_t)(variant&1);
        e->raw[ENT_PENDING_DAMAGE]=(uint8_t)((variant&2)?2:0);
        gaw_ram_write8(0xC621,(uint8_t)(variant%3));gaw_ram_write8(0xC600,103);
        gaw_ram_write8(0xC601,(uint8_t)((variant&4)?14:8));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,(uint8_t)slot);gaw_sms_compat_set_refresh_seed((uint8_t)variant);
        compare(slot,gaw_entity_handler_targets[103],handler);
    }
    unsigned bosses=cases;
    for(unsigned idx=0;idx<=10;++idx)for(unsigned state=0;state<=4;state+=2)
    for(unsigned variant=0;variant<16;++variant){
        setup();GawEntity *e=gaw_entity(16);e->raw[ENT_TYPE]=7;e->raw[ENT_STATE]=(uint8_t)state;
        e->raw[ENT_FLAGS]=0x43;e->raw[0x28]=counters[variant&3];e->raw[0x11]=0x50;e->raw[0x13]=0x80;
        for(unsigned i=24;i<32;++i)gaw_entity(i)->raw[ENT_TYPE]=(uint8_t)((variant&4)?102:0);
        gaw_ram_write8(0xC037,(uint8_t)idx);gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)(variant*47));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);gaw_sms_compat_set_refresh_seed((uint8_t)variant);compare(16,0x4BA4,handler);
    }
    /* Run every death countdown to its actual reward/ending handoff. */
    for(unsigned idx=0;idx<=10;++idx){
        setup();GawEntity *e=gaw_entity(16);e->raw[ENT_TYPE]=7;e->raw[ENT_FLAGS]=0x43;
        e->raw[0x11]=0x50;e->raw[0x13]=0x80;gaw_ram_write8(0xC037,(uint8_t)idx);
        for(unsigned tick=0;tick<182;++tick){
            gaw_sms_compat_set_refresh_seed((uint8_t)tick);compare(16,0x4BA4,handler);
        }
        assert(gaw_ram_read8((uint16_t)(0xC0CEu + idx))==1);
        assert(e->raw[ENT_TYPE]==(idx<10?15:0));
        if(idx==10)assert(gaw_ram_read8(RAM_MAIN_STATE)==14);
    }
    unsigned deaths=cases-bosses;
    for(unsigned type=3;type<=4;++type)for(unsigned state=0;state<=1;++state)
    for(unsigned variant=0;variant<64;++variant){
        setup();GawEntity *e=gaw_entity(1);e->raw[ENT_TYPE]=(uint8_t)type;e->raw[ENT_STATE]=(uint8_t)state;
        e->raw[ENT_DIRECTION]=(uint8_t)(variant&3);e->raw[0x11]=(uint8_t)((variant&4)?0xA0:0x50);
        e->raw[0x13]=(uint8_t)((variant&8)?0xF8:0x80);gaw_ram_write8(0xC0E4,(uint8_t)(1+(variant&1)));
        gaw_ram_write8(0xC0E5,(uint8_t)(1+(variant&1)));gaw_ram_write8(0xC0BA,(uint8_t)((variant&16)?1:0));
        if(variant&32)for(unsigned i=1;i<0x900;i+=2)gaw_ram_write8((uint16_t)(0xD600+i),0x80);
        gaw_ram_write16le(0xC034,0xDD00);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,1);
        compare(1,gaw_entity_handler_targets[type],handler);
    }
    unsigned before_homing=cases;
    /* Type 117: signed velocity limits, wall reversals, contact switching,
       returning-to-boss clearing and lifetime endpoints against real Z80. */
    const int16_t speeds[]={-768,-736,-1,0,1,736,767,768};
    const uint8_t positions[][2]={{0x1F,0x80},{0x20,0x27},{0x8F,0xD7},
                                 {0x90,0xD8},{0x50,0x80},{0x40,0x70}};
    const uint8_t life[]={1,47,48,192};
    for(unsigned state=2;state<=4;state+=2)
    for(unsigned speed=0;speed<8;++speed)for(unsigned position=0;position<6;++position)
    for(unsigned timer=0;timer<4;++timer)for(unsigned contact=0;contact<2;++contact){
        setup();GawEntity *e=gaw_entity(24),*boss=gaw_entity(16);
        e->raw[ENT_TYPE]=117;e->raw[ENT_STATE]=(uint8_t)state;
        e->raw[ENT_FLAGS]=(uint8_t)(0x13u|(contact?4u:0u));
        e->raw[0x11]=positions[position][0];e->raw[0x13]=positions[position][1];
        e->raw[0x22]=life[timer];
        gaw_entity_set16(e,ENT_DELTA0,(uint16_t)speeds[speed]);
        gaw_entity_set16(e,ENT_DELTA1,(uint16_t)-speeds[speed]);
        boss->raw[ENT_TYPE]=108;boss->raw[0x11]=0x40;boss->raw[0x13]=0x70;
        gaw_ram_write8(0xC311,0x70);gaw_ram_write8(0xC313,0x80);
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,24);
        compare(24,gaw_entity_handler_targets[117],handler);
    }
    unsigned homing_cases=cases-before_homing;
    unsigned before_drops=cases;
    const uint8_t saved_types[]={0,32,38,46,77,67,102,43,120,124,127};
    for(unsigned saved=0;saved<sizeof saved_types;++saved)for(unsigned interior=0;interior<2;++interior)
    for(unsigned full=0;full<2;++full)for(unsigned seed=0;seed<64;++seed){
        setup();GawEntity *e=gaw_entity(24);e->raw[ENT_TYPE]=1;e->raw[ENT_STATE]=2;e->raw[ENT_ANIM_FRAME]=4;
        e->raw[ENT_SAVED_TYPE]=saved_types[saved];e->raw[0x11]=0x50;e->raw[0x13]=0x80;
        gaw_ram_write8(0xC0BA,(uint8_t)interior);gaw_ram_write8(0xC0A2,1);
        for(unsigned i=9;i<16;++i)gaw_entity(i)->raw[ENT_TYPE]=(uint8_t)(full?8:0);
        gaw_sms_compat_set_refresh_seed((uint8_t)seed);compare(24,0x4AEE,handler);
    }
    printf("original-Z80 enemy/explosion loot differential: OK (%u cases)\n",cases-before_drops);
    printf("magic/boss original-Z80 differential: OK (%u boss phase + %u death/reward + %u spell projectile + %u homing projectile cases)\n",bosses,deaths,before_homing-bosses-deaths,homing_cases);
    return 0;
}
