/* Combat boundaries compared directly with unaccelerated original Z80. */
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
        fprintf(stderr,"combat case%u routine%04X slot%u RAM%04X original%02X native%02X\n",cases,target,slot,0xC000u+i,expected[i],gaw_ram[i]);assert(0);
    }
    ++cases;
}
static void handler(GawEntity *e){assert(gaw_entity_native_handler(e,e->raw[ENT_TYPE]));}
int main(void){
    const unsigned slots[]={0,1,9,16};
    const uint8_t boxes[]={0,1,5,47};
    const uint8_t positions[]={8,64,248};
    for(unsigned s=0;s<4;++s)for(unsigned b=0;b<4;++b)for(unsigned pos=0;pos<3;++pos)
    for(int distance=-24;distance<=24;distance+=8)for(unsigned gate=0;gate<8;++gate){
        setup();unsigned slot=slots[s],other=slot<9?9:0;
        GawEntity *e=gaw_entity(slot),*o=gaw_entity(other);
        e->raw[ENT_TYPE]=(uint8_t)(slot==0?2:38);e->raw[ENT_FLAGS]=3;
        e->raw[ENT_HITBOX_SOURCE]=boxes[b];e->raw[ENT_DEFENSE]=(uint8_t)(gate&1?8:0);
        e->raw[ENT_PENDING_DAMAGE]=(uint8_t)(gate&2?250:0);
        e->raw[0x11]=positions[pos];e->raw[0x13]=positions[pos];
        o->raw[ENT_TYPE]=(uint8_t)(gate&4?4:38);o->raw[ENT_FLAGS]=3;o->raw[ENT_ATTACK]=12;
        o->raw[ENT_HITBOX_TARGET]=boxes[b];o->raw[0x11]=(uint8_t)(positions[pos]+distance);o->raw[0x13]=positions[pos];
        if(gate==1)e->raw[ENT_HIT_FLASH_TIMER]=1;
        if(gate==2)o->raw[ENT_COOLDOWN]=1;
        if(gate==3)o->raw[ENT_FLAGS]=1;
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,(uint8_t)slot);
        gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)(slot+(gate==4?1:0)));
        compare(slot,0x2346,gaw_entity_collision_scan);
    }
    unsigned collisions=cases;
    const uint8_t flags[]={0,0x28,0x40};
    const uint8_t hp[]={0,2,6,24};
    const uint8_t damage[]={0,2,6,12,24,255};
    for(unsigned slot=0;slot<=16;slot+=16)for(unsigned f=0;f<3;++f)for(unsigned h=0;h<4;++h)
    for(unsigned d=0;d<6;++d)for(unsigned direction=0;direction<4;++direction)for(unsigned blocked=0;blocked<2;++blocked){
        setup();GawEntity *e=gaw_entity(slot),*o=gaw_entity(slot?0:16);
        e->raw[ENT_TYPE]=(uint8_t)(slot?38:2);e->raw[ENT_FLAGS]=flags[f];
        e->raw[ENT_HP]=hp[h];e->raw[ENT_PENDING_DAMAGE]=damage[d];
        e->raw[0x11]=0x60;e->raw[0x13]=0x70;
        e->raw[ENT_DEFENSE]=(uint8_t)(blocked?8:0);
        o->raw[ENT_TYPE]=(uint8_t)(blocked?2:4);o->raw[ENT_DIRECTION]=(uint8_t)direction;
        gaw_entity_set16(e,ENT_RELATED_PTR,gaw_entity_addr(o));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,(uint8_t)slot);
        if(blocked)for(unsigned i=1;i<0x900;i+=2)gaw_ram_write8((uint16_t)(0xD600+i),0x80);
        compare(slot,0x2768,gaw_entity_apply_pending_damage);
    }
    unsigned damage_cases=cases-collisions;
    const uint8_t states[]={0,2,4,6,8,10,12};
    for(unsigned type=32;type<=38;type+=6)for(unsigned st=0;st<(type==32?7u:5u);++st)
    for(unsigned phase=0;phase<2;++phase)for(unsigned dir=0;dir<4;++dir)
    for(unsigned variant=0;variant<12;++variant){
        setup();GawEntity *e=gaw_entity(16);
        e->raw[ENT_TYPE]=(uint8_t)type;e->raw[ENT_STATE]=states[st];e->raw[ENT_FLAGS]=0x2B;
        e->raw[ENT_HP]=(uint8_t)(type==38?2:6);e->raw[ENT_ATTACK]=(uint8_t)(type==38?2:4);
        e->raw[ENT_DIRECTION]=(uint8_t)dir;e->raw[ENT_MOTION_PHASE]=(uint8_t)phase;
        e->raw[ENT_ANIM_FRAME]=(uint8_t)(variant&1?3:0);e->raw[0x20]=(uint8_t)(variant/4u);
        e->raw[0x11]=0x60;e->raw[0x13]=0x70;
        e->raw[ENT_PENDING_DAMAGE]=(uint8_t)(variant&2?1:0);
        gaw_ram_write8(0xC311,0x60);gaw_ram_write8(0xC313,(uint8_t)(variant&1?0x90:0x70));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
        gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)(variant*47u));
        compare(16,gaw_entity_handler_targets[type],handler);
    }
    unsigned ai_cases=cases-collisions-damage_cases;
    /* An attached type-91 enemy may die while the hero remains grabbed.
     * Preserve the original behavior; the controller must escape first. */
    for(unsigned pending=0;pending<=18;pending+=9)
    for(unsigned player_state=1;player_state<=12;player_state+=11){
        setup();GawEntity *e=gaw_entity(16),*hero=gaw_entity(0);
        hero->raw[ENT_TYPE]=2;hero->raw[ENT_STATE]=(uint8_t)player_state;
        hero->raw[ENT_HP]=128;hero->raw[0x11]=80;hero->raw[0x13]=120;
        e->raw[ENT_TYPE]=91;e->raw[ENT_STATE]=12;e->raw[ENT_FLAGS]=0x2B;
        e->raw[ENT_HP]=18;e->raw[ENT_PENDING_DAMAGE]=(uint8_t)pending;
        e->raw[0x11]=88;e->raw[0x13]=120;e->raw[0x21]=16;
        gaw_entity_set16(e,ENT_RELATED_PTR,gaw_entity_addr(hero));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
        compare(16,gaw_entity_handler_targets[91],handler);
        compare(16,0x2768,gaw_entity_apply_pending_damage);
        if(pending==18){assert(e->raw[ENT_TYPE]!=91);assert(hero->raw[ENT_STATE]==12);}
    }
    unsigned grab_cases=cases-collisions-damage_cases-ai_cases;
    /* $5049 rejects hits unless the hero faces opposite types 92/93. */
    for(unsigned type=92;type<=93;++type)for(unsigned facing=0;facing<4;++facing)
    for(unsigned hero_facing=0;hero_facing<4;++hero_facing){
        static const uint8_t opposite[4]={1,0,3,2};
        setup();GawEntity *e=gaw_entity(16);
        e->raw[ENT_TYPE]=(uint8_t)type;e->raw[ENT_STATE]=8;
        e->raw[ENT_FLAGS]=0x2B;e->raw[ENT_HP]=36;
        e->raw[ENT_PENDING_DAMAGE]=8;e->raw[ENT_MOTION_PHASE]=1;
        e->raw[ENT_DIRECTION]=(uint8_t)facing;
        gaw_ram_write8(0xC30A,(uint8_t)hero_facing);
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
        compare(16,gaw_entity_handler_targets[type],handler);
        assert(e->raw[ENT_PENDING_DAMAGE]==(hero_facing==opposite[facing]?8u:0u));
    }
    unsigned directional_cases=cases-collisions-damage_cases-ai_cases-grab_cases;
    /* Fire stops at 80/A0 terrain, but crosses E0 partitions. */
    const uint8_t terrain[]={0x00,0x80,0xA0,0xE0};
    for(unsigned t=0;t<4;++t)for(unsigned facing=0;facing<4;++facing){
        setup();GawEntity *e=gaw_entity(1);
        e->raw[ENT_TYPE]=3;e->raw[ENT_STATE]=1;e->raw[ENT_FLAGS]=3;
        e->raw[ENT_DIRECTION]=(uint8_t)facing;e->raw[0x11]=80;e->raw[0x13]=128;
        for(unsigned i=1;i<1536u;i+=2)gaw_ram_write8((uint16_t)(0xD600u+i),terrain[t]);
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,1);
        compare(1,gaw_entity_handler_targets[3],handler);
        assert(e->raw[ENT_TYPE]==(t==1u||t==2u?0u:3u));
    }
    unsigned fire_cases=cases-collisions-damage_cases-ai_cases-grab_cases-directional_cases;
    unsigned before_geometry=cases;
    /* Large actor boxes against every axe-2 weapon pose, on both axes.
       Compare receiving-player and receiving-boss scans with original $2346. */
    const int gaps[]={-40,-32,-28,-24,-16,0,16,24,28,32,40};
    for(unsigned box=40;box<=44;++box)for(unsigned weapon=14;weapon<=25;++weapon)
    for(unsigned axis=0;axis<2;++axis)for(unsigned gap=0;gap<11;++gap)
    for(unsigned slot=0;slot<=16;slot+=16){
        setup();GawEntity *hero=gaw_entity(0),*boss=gaw_entity(16);
        hero->raw[ENT_TYPE]=2;boss->raw[ENT_TYPE]=108;
        hero->raw[ENT_FLAGS]=boss->raw[ENT_FLAGS]=3;
        hero->raw[ENT_ATTACK]=12;hero->raw[ENT_DEFENSE]=12;
        boss->raw[ENT_ATTACK]=30;boss->raw[ENT_DEFENSE]=6;
        hero->raw[ENT_HITBOX_SOURCE]=5;hero->raw[ENT_HITBOX_TARGET]=(uint8_t)weapon;
        boss->raw[ENT_HITBOX_SOURCE]=boss->raw[ENT_HITBOX_TARGET]=(uint8_t)box;
        boss->raw[0x13]=128;boss->raw[0x11]=80;
        hero->raw[0x13]=(uint8_t)(128+(axis==0?gaps[gap]:0));
        hero->raw[0x11]=(uint8_t)(80+(axis==1?gaps[gap]:0));
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,(uint8_t)slot);
        gaw_ram_write8(RAM_FRAME_COUNTER,(uint8_t)slot);
        compare(slot,0x2346,gaw_entity_collision_scan);
    }
    unsigned geometry_cases=cases-before_geometry,before_curse=cases;
    const uint8_t contact_flags[]={0,1,2,3,4,7,0x2B,0xFF};
    const uint8_t curses[]={0,1,2,255};
    for(unsigned st=8;st<=10;st+=2)for(unsigned phase=0;phase<2;++phase)
    for(unsigned dir=0;dir<4;++dir)for(unsigned f=0;f<8;++f)for(unsigned c=0;c<4;++c){
        setup();GawEntity *e=gaw_entity(16);
        e->raw[ENT_TYPE]=83;e->raw[ENT_STATE]=(uint8_t)st;
        e->raw[ENT_MOTION_PHASE]=(uint8_t)phase;e->raw[ENT_DIRECTION]=(uint8_t)dir;
        e->raw[ENT_FLAGS]=contact_flags[f];e->raw[ENT_HP]=18;
        e->raw[0x11]=96;e->raw[0x13]=80;
        gaw_ram_write8(0xC311,64);gaw_ram_write8(0xC313,128);
        gaw_ram_write8(0xC0BF,curses[c]);gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
        compare(16,0x4FF3,handler);
    }
    printf("combat original-Z80 differential: OK (%u collision + %u damage/death/recoil + %u entropy-replayed AI + %u grab/death + %u directional-defense + %u fire-terrain + %u large-actor geometry + %u curse-wrapper cases)\n",collisions,damage_cases,ai_cases,grab_cases,directional_cases,fire_cases,geometry_cases,cases-before_curse);
    return 0;
}
