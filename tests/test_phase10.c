#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_entity.h"
#include "gaw_host.h"
#include "gaw_ram.h"

static void reset_all(void) { memset(gaw_ram,0,sizeof gaw_ram); gaw_host_set_entropy(0x5A); }

static void test_type32_spawn_and_init(void) {
    reset_all(); GawEntity *p=gaw_entity(0), *e=gaw_entity(16);
    p->raw[0x11]=0x80; p->raw[0x13]=0x80;
    e->raw[ENT_TYPE]=32; gaw_ram_write8(0xC046,16); gaw_ram_write8(0xC02F,0);
    /* entropy $21 -> packed cell $31; tile 0 is allowed by $586D. */
    gaw_host_set_entropy(0x21);
    assert(gaw_entity_native_handler(e,32)==1);
    assert(e->raw[ENT_STATE]==2 && e->raw[0x08]==0xFA && e->raw[0x09]==0x84);
    assert(e->raw[0x11]==0x40 && e->raw[0x13]==0x18);
    assert((e->raw[ENT_FLAGS]&3u)==3u);
}

static void test_type32_walk_aim_fire(void) {
    reset_all(); GawEntity *p=gaw_entity(0), *e=gaw_entity(16);
    e->raw[ENT_TYPE]=32; e->raw[ENT_STATE]=2; e->raw[ENT_ANIM_FRAME]=3;
    e->raw[0x11]=0x50; e->raw[0x13]=0x60;
    assert(gaw_entity_native_handler(e,32));
    assert(e->raw[ENT_STATE]==4 && e->raw[ENT_ANIM_FRAME]==0 && e->raw[0x08]==0x2E && e->raw[0x09]==0x85);

    /* state 4, R&3 == 0, empty map -> left motion from $85D9. */
    gaw_host_set_entropy(0); assert(gaw_entity_native_handler(e,32));
    assert(e->raw[ENT_STATE]==8 && e->raw[ENT_DIRECTION]==0 && e->raw[ENT_MOTION_PHASE]==0x10);
    assert(gaw_entity_get16(e,ENT_DELTA0)==0xFF80 && gaw_entity_get16(e,ENT_DELTA1)==0);

    /* state 8, R&0f == 8, same row -> face right toward Arthur and aim. */
    e->raw[ENT_MOTION_PHASE]=0; p->raw[0x11]=0x80; p->raw[0x13]=0x60; gaw_host_set_entropy(8);
    assert(gaw_entity_native_handler(e,32));
    assert(e->raw[ENT_STATE]==0x0A && e->raw[ENT_DIRECTION]==1 && e->raw[ENT_MOTION_PHASE]==0x10);
    assert(gaw_entity_get16(e,ENT_DELTA0)==0 && gaw_entity_get16(e,ENT_DELTA1)==0);

    /* Fire after the 16-tick aim pause: type 32 maps to auxiliary type 16. */
    e->raw[ENT_MOTION_PHASE]=0; assert(gaw_entity_native_handler(e,32));
    assert(e->raw[ENT_STATE]==0x0C && e->raw[ENT_MOTION_PHASE]==8);
    assert(gaw_entity(24)->raw[ENT_TYPE]==16);
    assert(gaw_entity(24)->raw[0x11]==e->raw[0x11] && gaw_entity(24)->raw[0x13]==e->raw[0x13]);
    assert(gaw_entity(24)->raw[ENT_DIRECTION]==1);
    e->raw[ENT_MOTION_PHASE]=0; assert(gaw_entity_native_handler(e,32)); assert(e->raw[ENT_STATE]==4);
}

static void test_all_32_native(void) {
    for (uint8_t type=1;type<=32;++type) {
        reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=type; e->raw[0x11]=0x50; e->raw[0x13]=0x60;
        gaw_entity(0)->raw[0x11]=0x80; gaw_entity(0)->raw[0x13]=0x80; gaw_ram_write8(0xC037,1);
        assert(gaw_entity_native_handler(e,type)==1);
    }
}
int main(void) { test_type32_spawn_and_init(); test_type32_walk_aim_fire(); test_all_32_native(); puts("phase10 tests: OK"); return 0; }
