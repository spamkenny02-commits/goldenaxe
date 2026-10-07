#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_entity.h"
#include "gaw_host.h"
#include "gaw_platform.h"
#include "gaw_ram.h"

static void reset_all(void) { gaw_platform_init(); memset(gaw_ram,0,sizeof gaw_ram); gaw_host_set_entropy(0x5A); gaw_ram_write8(0xDE05,0x80); }

static void test_action_type3_native(void) {
    reset_all(); GawEntity *e=gaw_entity(1);
    e->raw[ENT_TYPE]=3; e->raw[ENT_STATE]=0; e->raw[ENT_DIRECTION]=0; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    gaw_ram_write8(0xC0E4,1);
    assert(gaw_entity_native_handler(e,3));
    assert(e->raw[ENT_STATE]==1 && e->raw[ENT_FLAGS]==3 && e->raw[ENT_MOTION_PHASE]==2);
    assert(e->raw[0x08]==0x11 && e->raw[0x09]==0x84);
    assert(e->raw[ENT_DELTA0+1]==0xFD && e->raw[ENT_DELTA1+1]==0x00);
    assert(e->raw[0x11]==0x48 && e->raw[0x13]==0x60);
}

static void test_action_type5_native(void) {
    reset_all(); GawEntity *e=gaw_entity(1);
    e->raw[ENT_TYPE]=5; e->raw[ENT_DIRECTION]=1; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    gaw_ram_write8(0xC0E0,2); /* attack table -> 6 */
    assert(gaw_entity_native_handler(e,5));
    assert(e->raw[ENT_STATE]==1 && e->raw[ENT_MOTION_PHASE]==8 && e->raw[ENT_ATTACK]==6);
    assert(e->raw[0x11]==0x4E);
    assert(e->raw[ENT_DELTA0+1]==0x04 && e->raw[ENT_DELTA1+1]==0x00);
}

static void test_resource_pickups_native(void) {
    reset_all(); GawEntity *p=gaw_entity(0), *e=gaw_entity(9);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    e->raw[ENT_TYPE]=11; e->raw[ENT_STATE]=0;
    assert(gaw_entity_native_handler(e,11));
    assert(gaw_ram_read8(0xC0A3)==0x1B && e->raw[ENT_STATE]==2 && e->raw[ENT_GFX_ID]==0xBC);
    e->raw[ENT_PENDING_DAMAGE]=1; gaw_ram_write8(0xC0DA,40); gaw_ram_write8(0xC318,10);
    assert(gaw_entity_native_handler(e,11));
    assert(e->raw[ENT_TYPE]==0 && gaw_ram_read8(0xC318)==34);

    reset_all(); e=gaw_entity(9); e->raw[ENT_TYPE]=12; e->raw[ENT_STATE]=2; e->raw[ENT_PENDING_DAMAGE]=1;
    gaw_ram_write8(0xC0DB,5); gaw_ram_write8(0xC0DC,10);
    assert(gaw_entity_native_handler(e,12)); assert(gaw_ram_read8(0xC0DB)==10);

    reset_all(); e=gaw_entity(9); e->raw[ENT_TYPE]=13; e->raw[ENT_STATE]=2; e->raw[ENT_PENDING_DAMAGE]=1;
    gaw_entity(16)->raw[ENT_TYPE]=0x20; gaw_entity(17)->raw[ENT_TYPE]=0x1F;
    assert(gaw_entity_native_handler(e,13)); assert(gaw_entity(16)->raw[ENT_COOLDOWN]==0xFF); assert(gaw_entity(17)->raw[ENT_COOLDOWN]==0);
}

static void test_death_handlers_native(void) {
    reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=1; e->raw[ENT_STATE]=0;
    assert(gaw_entity_native_handler(e,1)); assert(e->raw[ENT_STATE]==2 && e->raw[ENT_ANIM_FRAMES]==5);
    e->raw[ENT_ANIM_FRAME]=4; e->raw[ENT_SAVED_TYPE]=0; gaw_ram_write8(0xC0A2,3);
    assert(gaw_entity_native_handler(e,1)); /* Original $4B3F jumps directly to clear for visual explosions. */
    assert(e->raw[ENT_TYPE]==0 && gaw_ram_read8(0xC0A2)==3);

    reset_all(); e=gaw_entity(16); e->raw[ENT_TYPE]=7; gaw_ram_write8(0xC037,3); e->raw[ENT_FLAGS]=0xFF;
    assert(gaw_entity_native_handler(e,7)); assert(e->raw[ENT_STATE]==2 && e->raw[0x28]==0xB4); assert(gaw_ram_read8(0xC0D1)==1);
    e->raw[ENT_STATE]=4; assert(gaw_entity_native_handler(e,7)); assert(e->raw[ENT_TYPE]==0x0F && e->raw[ENT_STATE]==0);
}

static void test_entity27_map_cull(void) {
    reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=27; e->raw[ENT_STATE]=2; e->raw[ENT_MOTION_PHASE]=1; e->raw[0x11]=0x40; e->raw[0x13]=0x40;
    /* $230E with B=0,C=-4 -> $D7D0. */
    gaw_ram_write16le(0xD7D0,0x8000);
    assert(gaw_entity_native_handler(e,27)); assert(e->raw[ENT_TYPE]==0);
}

static void test_entity28_retarget(void) {
    reset_all(); GawEntity *p=gaw_entity(0), *e=gaw_entity(16);
    p->raw[0x11]=0x70; p->raw[0x13]=0x70;
    e->raw[ENT_TYPE]=28; e->raw[0x11]=0x60; e->raw[0x13]=0x60;
    assert(gaw_entity_native_handler(e,28));
    assert(e->raw[ENT_STATE]==4 && e->raw[ENT_MOTION_PHASE]==0x10 && e->raw[0x20]==8);
    assert(e->raw[0x08]==0x06 && e->raw[0x09]==0x90 && e->raw[ENT_ATTACK]==0x10);
    assert(e->raw[0x11]==0x4C);
}

static void test_ballistic_entities_native(void) {
    reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=29; e->raw[ENT_DIRECTION]=0; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    assert(gaw_entity_native_handler(e,29));
    assert(e->raw[ENT_STATE]==4 && e->raw[ENT_DIRECTION]==2);
    assert(gaw_entity_get16(e,0x28)==0x01F0 && gaw_entity_get16(e,0x2A)==0x01F0);
    assert(gaw_entity_get16(e,ENT_ACCUM0)==0x4E10 && gaw_entity_get16(e,ENT_ACCUM1)==0x5FA0);

    reset_all(); GawEntity *p=gaw_entity(0); e=gaw_entity(16); p->raw[0x11]=0x70; p->raw[0x13]=0x70;
    e->raw[ENT_TYPE]=31; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    assert(gaw_entity_native_handler(e,31));
    assert(e->raw[ENT_STATE]==6 && e->raw[ENT_MOTION_PHASE]==0x60);
    assert(e->raw[0x08]==0xA2 && e->raw[0x09]==0x90 && e->raw[ENT_ATTACK]==0x10);
    assert(gaw_entity_get16(e,0x2E)==0xFFD8);
}


static void test_action_type4_world_native(void) {
    reset_all(); GawEntity *e=gaw_entity(1);
    e->raw[ENT_TYPE]=4; e->raw[ENT_DIRECTION]=0; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    gaw_ram_write8(0xC0BA,1); /* use $3AD9 transformation list */
    gaw_ram_write8(0xDC45,0x0B);
    assert(gaw_entity_native_handler(e,4));
    assert(e->raw[ENT_STATE]==1 && e->raw[ENT_MOTION_PHASE]==2 && e->raw[0x08]==0x61 && e->raw[0x09]==0x84);
    assert(gaw_ram_read8(0xDC45)==0x00);
}

static void test_special_pickup15_native(void) {
    reset_all(); GawEntity *e=gaw_entity(9); e->raw[ENT_TYPE]=15;
    gaw_ram_write8(0xC037,1); gaw_ram_write8(0xC0DA,0x20); gaw_ram_write8(0xC0DC,0x30); gaw_ram_write8(0xC318,5);
    assert(gaw_entity_native_handler(e,15));
    assert(e->raw[ENT_STATE]==2 && e->raw[ENT_GFX_ID]==0x85 && e->raw[0x11]==0x1C && e->raw[0x13]==0x80);
    e->raw[ENT_PENDING_DAMAGE]=1;
    gaw_host_queue_pad(220,0x20);gaw_host_queue_pad(221,0);
    assert(gaw_entity_native_handler(e,15));
    assert(gaw_ram_read8(0xC0CF)==0x80 && gaw_ram_read8(0xC0A3)==0x24);
    assert(gaw_ram_read8(0xC0DA)==0x28 && gaw_ram_read8(0xC0DB)==0x30 && gaw_ram_read8(0xC318)==0x28);
}


static void test_native_coverage_first32(void) {
    for (uint8_t type=1; type<=31; ++type) {
        reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=type; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
        gaw_entity(0)->raw[0x11]=0x60; gaw_entity(0)->raw[0x13]=0x70; gaw_ram_write8(0xC037,1);
        assert(gaw_entity_native_handler(e,type)==1);
    }
    reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=32;
    /* Coverage expanded after the original phase-9 milestone. */
    assert(gaw_entity_native_handler(e,32)==1);
}

int main(void) {
    test_action_type3_native(); test_action_type4_world_native(); test_action_type5_native(); test_resource_pickups_native(); test_special_pickup15_native();
    test_death_handlers_native(); test_entity27_map_cull(); test_entity28_retarget(); test_ballistic_entities_native(); test_native_coverage_first32();
    puts("phase9 tests: OK"); return 0;
}
