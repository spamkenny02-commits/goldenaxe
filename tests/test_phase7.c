#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_entity.h"
#include "gaw_host.h"
#include "gaw_player.h"
#include "gaw_ram.h"
#include "gaw_tables.h"
#include "gaw_world_progress.h"

static void test_input_edges(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    gaw_vblank_tick(0x11);
    assert(gaw_ram_read8(RAM_INPUT_HELD) == 0x11);
    assert(gaw_ram_read8(RAM_INPUT_PRESSED) == 0x11);
    gaw_vblank_tick(0x11);
    assert(gaw_ram_read8(RAM_INPUT_PRESSED) == 0x00);
    gaw_vblank_tick(0x10);
    assert(gaw_ram_read8(RAM_INPUT_PRESSED) == 0x00);
    gaw_vblank_tick(0x11);
    assert(gaw_ram_read8(RAM_INPUT_PRESSED) == 0x01);
}

static void test_pause_nmi(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    gaw_nmi_pause();
    assert(gaw_ram_read8(RAM_PAUSE_NMI_COUNTER) == 0x14);
    gaw_vblank_tick(0);
    assert(gaw_ram_read8(RAM_PAUSE_HELD) == 1);
    assert(gaw_ram_read8(RAM_PAUSE_PRESSED) == 1);
    gaw_vblank_tick(0);
    assert(gaw_ram_read8(RAM_PAUSE_PRESSED) == 0);
}

static void test_world_table(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    gaw_ram_write16le(RAM_WORLD_CELL_ID, 0);
    gaw_world_select_callback();
    assert(gaw_ram_read16le(RAM_WORLD_CALLBACK) == 0xAC27);
    gaw_ram_write16le(RAM_WORLD_CELL_ID, 5);
    gaw_world_select_callback();
    assert(gaw_ram_read16le(RAM_WORLD_CALLBACK) == 0x65D0);
}

static void test_entity_core(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *e = gaw_entity(0);
    e->raw[ENT_TYPE] = 2;
    e->raw[ENT_MOTION_PHASE] = 2;
    e->raw[ENT_ANIM_FRAMES] = 3;
    e->raw[ENT_ANIM_DELAY] = 1;
    gaw_entity_set16(e, ENT_ACCUM0, 0x0102);
    gaw_entity_set16(e, ENT_DELTA0, 0x0003);
    gaw_entity_set16(e, ENT_ACCUM1, 0x0204);
    gaw_entity_set16(e, ENT_DELTA1, 0x0005);
    gaw_entities_update_all();
    assert(gaw_ram_read8(RAM_ACTIVE_ENTITY_COUNT) == 1);
    assert(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX) == 32);
    assert(e->raw[ENT_MOTION_PHASE] == 1);
    assert(gaw_entity_get16(e, ENT_ACCUM0) == 0x0105);
    assert(gaw_entity_get16(e, ENT_ACCUM1) == 0x0209);
    assert(e->raw[ENT_ANIM_FRAME] == 1);
}

static void test_damage_saturates(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *e = gaw_entity(0);
    e->raw[ENT_TYPE] = 2;
    e->raw[ENT_HP] = 3;
    e->raw[ENT_PENDING_DAMAGE] = 5;
    gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, 0);
    gaw_entity_apply_pending_damage(e);
    assert(e->raw[ENT_HP] == 0);
    assert(e->raw[ENT_PENDING_DAMAGE] == 0);
}

static void test_gameplay_init_and_state(void) {
    memset(gaw_ram, 0xA5, sizeof gaw_ram);
    gaw_ram_write8(RAM_MAIN_STATE, 0x0A);
    gaw_state_gameplay_init();
    assert(gaw_ram_read8(RAM_MAIN_STATE) == 0x0C);
    for (unsigned a=0xC090; a<0xC0B0; ++a) assert(gaw_ram_read8((uint16_t)a)==0);
    for (unsigned a=0xC4B0; a<0xC600; ++a) assert(gaw_ram_read8((uint16_t)a)==0);
}

static void test_gameplay_state_transitions(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    gaw_ram_write8(RAM_MAIN_STATE, 0x0C);
    gaw_ram_write8(0xC318, 1);
    gaw_host_set_pad(0x10);
    gaw_state_gameplay();
    assert(gaw_ram_read8(RAM_MAIN_STATE) == 0x10);

    memset(gaw_ram, 0, sizeof gaw_ram);
    gaw_ram_write8(RAM_MAIN_STATE, 0x0C);
    gaw_ram_write8(0xC318, 1);
    gaw_host_set_pad(0);
    gaw_nmi_pause();
    gaw_state_gameplay();
    assert(gaw_ram_read8(RAM_MAIN_STATE) == 0x02);
}


static void test_collision_player_pickup(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *player = gaw_entity(0);
    GawEntity *pickup = gaw_entity(9);
    player->raw[ENT_TYPE] = 2;
    player->raw[ENT_STATE] = 1;
    player->raw[ENT_FLAGS] = 0x02;
    player->raw[ENT_HITBOX_SOURCE] = 1;
    player->raw[0x11] = 0x40;
    player->raw[0x13] = 0x40;
    pickup->raw[ENT_TYPE] = 8;
    pickup->raw[ENT_STATE] = 2;
    pickup->raw[ENT_FLAGS] = 0x02;
    pickup->raw[ENT_HITBOX_TARGET] = 1;
    pickup->raw[0x11] = 0x40;
    pickup->raw[0x13] = 0x40;
    gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, 0);
    gaw_ram_write8(RAM_FRAME_COUNTER, 0);
    gaw_entity_collision_scan(player);
    assert(gaw_entity_get16(player, ENT_RELATED_PTR) == gaw_entity_addr(pickup));
    assert(player->raw[ENT_PENDING_DAMAGE] == 0); /* player touching pickup */
    assert((pickup->raw[ENT_FLAGS] & 0x04u) != 0);
}

static void test_collision_damage(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *victim = gaw_entity(16);
    GawEntity *attacker = gaw_entity(0);
    victim->raw[ENT_TYPE] = 16;
    victim->raw[ENT_FLAGS] = 0x02;
    victim->raw[ENT_HITBOX_SOURCE] = 1;
    victim->raw[ENT_DEFENSE] = 3;
    victim->raw[0x11] = victim->raw[0x13] = 0x50;
    attacker->raw[ENT_TYPE] = 2;
    attacker->raw[ENT_FLAGS] = 0x02;
    attacker->raw[ENT_HITBOX_TARGET] = 1;
    attacker->raw[ENT_ATTACK] = 9;
    attacker->raw[0x11] = attacker->raw[0x13] = 0x50;
    gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, 16);
    gaw_ram_write8(RAM_FRAME_COUNTER, 0);
    gaw_entity_collision_scan(victim);
    assert(victim->raw[ENT_PENDING_DAMAGE] == 6);
    assert(gaw_entity_get16(victim, ENT_RELATED_PTR) == gaw_entity_addr(attacker));
}

static void test_pickup_reward_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *player = gaw_entity(0);
    GawEntity *pickup = gaw_entity(9);
    player->raw[ENT_TYPE] = 2;
    player->raw[ENT_STATE] = 1;
    player->raw[ENT_FLAGS] = 0x02;
    player->raw[ENT_HITBOX_SOURCE] = 1;
    player->raw[0x11] = player->raw[0x13] = 0x40;
    pickup->raw[ENT_TYPE] = 8;
    pickup->raw[ENT_STATE] = 2;
    pickup->raw[ENT_FLAGS] = 0x02;
    pickup->raw[ENT_HITBOX_TARGET] = 1;
    pickup->raw[0x11] = pickup->raw[0x13] = 0x40;
    gaw_ram_write8(0xC0DD, 7);
    gaw_ram_write8(RAM_FRAME_COUNTER, 0);
    gaw_entities_update_all();
    assert(pickup->raw[ENT_TYPE] == 0);
    assert(gaw_ram_read8(0xC0DD) == 8);
    assert(gaw_ram_read8(0xDE08) == 0x96);
}

static void test_enemy_init_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *e = gaw_entity(16);
    e->raw[ENT_TYPE] = 16;
    e->raw[ENT_STATE] = 0;
    e->raw[ENT_DIRECTION] = 0;
    e->raw[0x11] = 0x50;
    e->raw[0x13] = 0x60;
    assert(gaw_entity_native_handler(e,16));
    assert(e->raw[ENT_STATE] == 2);
    assert(e->raw[ENT_FLAGS] == 0x13);
    assert(e->raw[ENT_MOTION_PHASE] == 0x80);
    assert(e->raw[0x08] == 0xD4 && e->raw[0x09] == 0x8E);
    assert(e->raw[ENT_ATTACK] == 4);
    assert(e->raw[0x11] == 0x48);
    assert(gaw_entity_get16(e, ENT_DELTA0) == 0xFE80);
    assert(gaw_entity_get16(e, ENT_DELTA1) == 0x0000);
}

static void test_enemy_cull_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *e = gaw_entity(16);
    e->raw[ENT_TYPE] = 16;
    e->raw[ENT_STATE] = 2;
    e->raw[ENT_MOTION_PHASE] = 1;
    e->raw[0x11] = 7;
    e->raw[0x13] = 0x40;
    assert(gaw_entity_native_handler(e,16));
    assert(e->raw[ENT_TYPE] == 0);
}


static void test_player_walk_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *p = gaw_entity(0);
    p->raw[ENT_TYPE]=2;
    p->raw[ENT_STATE]=1;
    p->raw[ENT_HP]=10;
    p->raw[ENT_DIRECTION]=0;
    gaw_ram_write8(RAM_PLAYER_ENV_MODE,0);
    gaw_ram_write8(RAM_INPUT_HELD,1); /* first directional bit */
    assert(gaw_entity_native_handler(p,2));
    assert(p->raw[ENT_MOTION_PHASE]==5);
    assert(p->raw[ENT_DIRECTION]==0);
    assert(gaw_entity_get16(p,ENT_DELTA0)==0xFE67);
    assert(gaw_entity_get16(p,ENT_DELTA1)==0x0000);
    assert(gaw_ram_read16le(RAM_PLAYER_MOTION_PTR)==0x33DC);
    assert(gaw_ram_read16le(RAM_PLAYER_SPRITE_PTR)==0x81C3);
    assert(gaw_ram_read8(RAM_PLAYER_SPRITE_BANK)==4);
}

static void test_player_collision_deflection_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *p = gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write8(RAM_INPUT_HELD,1);
    /* $2C8D rebuilds C048 from D600. For x=y=$40, the cache begins at $D78B.
       Requested direction 0: +3 blocked, +5 open, +15 open -> resolve to 3. */
    gaw_ram_write8(0xD78E,0x80);
    assert(gaw_entity_native_handler(p,2));
    assert(p->raw[ENT_DIRECTION]==3);
    assert(gaw_ram_read8(RAM_PLAYER_FORCED_DIR)==0x80);
    assert(gaw_entity_get16(p,ENT_DELTA0)==0x0000);
    assert(gaw_entity_get16(p,ENT_DELTA1)==0x019A);
}

static void test_player_action_animation_native(void) {
    memset(gaw_ram, 0, sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    gaw_ram_write8(0xC0DF,0); /* action table entry $2FAA */
    gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    assert(gaw_entity_native_handler(p,2));
    assert(p->raw[ENT_STATE]==3);
    assert(p->raw[ENT_ANIM_TICK]==0);
    assert(p->raw[ENT_ANIM_FRAME]==4);
}

static void test_player_heal_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=20;
    gaw_ram_write8(0xC0DF,7);
    gaw_ram_write8(0xC0DB,30);
    gaw_ram_write8(0xC0DA,40);
    gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    assert(gaw_entity_native_handler(p,2));
    assert(gaw_ram_read8(0xC0DB)==6);
    assert(p->raw[ENT_HP]==36);
}

static void test_player_death_states_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=8; p->raw[ENT_HP]=0; p->raw[ENT_FLAGS]=3;
    gaw_player_handler(p);
    assert(p->raw[ENT_STATE]==9);
    assert(p->raw[ENT_MOTION_PHASE]==0x5A);
    assert((p->raw[ENT_FLAGS]&2u)==0);
    assert(gaw_ram_read16le(RAM_PLAYER_SPRITE_PTR)==0xA140);
    p->raw[ENT_MOTION_PHASE]=0;
    gaw_player_handler(p);
    assert(gaw_ram_read8(RAM_MAIN_STATE)==0x14);
}


static void test_player_full_entity_pass_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10; p->raw[ENT_FLAGS]=0;
    p->raw[ENT_ACCUM0]=0; p->raw[ENT_ACCUM0+1]=0x40;
    p->raw[ENT_ACCUM1]=0; p->raw[ENT_ACCUM1+1]=0x50;
    gaw_ram_write8(RAM_INPUT_HELD,1);
    gaw_ram_write8(RAM_PLAYER_ENV_MODE,0);
    gaw_entities_update_all();
    assert(p->raw[ENT_MOTION_PHASE]==4); /* handler sets 5, common motion decrements */
    assert(gaw_entity_get16(p,ENT_DELTA0)==0xFE67);
    assert(gaw_entity_get16(p,ENT_ACCUM0)==0x3E67);
    assert(gaw_ram_read8(RAM_ACTIVE_ENTITY_COUNT)==1);
}


static void test_player_environment_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=7; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write8(0xC090,1);
    gaw_ram_write8(0xC0EC,1);
    gaw_ram_write8(0xC0F2,2); gaw_ram_write8(0xC0F1,3);
    gaw_ram_write8(0xC0DF,0); gaw_ram_write8(0xC0E0,1);
    /* Cache starts at D78B. C052/C054 are offsets 10/12 -> D7CD/D7CF. */
    gaw_ram_write8(0xD78B,0x12);
    gaw_ram_write8(0xD7CD,0xA0); gaw_ram_write8(0xD7CF,0xA0);
    gaw_player_handler(p);
    assert(gaw_ram_read8(RAM_PLAYER_TILE_FLAGS)==0x12);
    assert(gaw_ram_read8(RAM_PLAYER_ENV_MODE)==2);
    assert(p->raw[ENT_DEFENSE]==10);
    assert(p->raw[ENT_ATTACK]==2);
}

static void test_player_map_mutation_38ac_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x48; p->raw[0x13]=0x48;
    gaw_ram_write8(0xC0ED,1); gaw_ram_write8(RAM_INPUT_HELD,1);
    gaw_ram_write8(0xDC34,0x02); gaw_ram_write8(0xDC24,0x0C); gaw_ram_write8(0xDC14,0x0C);
    gaw_player_handler(p);
    assert(gaw_ram_read8(0xDC34)==0x6D);
    assert(gaw_ram_read8(0xDC24)==0x6C);
    assert(gaw_ram_read8(0xDC14)==0x6C);
    assert(gaw_ram_read16le(0xC098)==0x0603);
    assert(gaw_ram_read8(0xC09A)==0x38 && gaw_ram_read8(0xC09B)==0x40);
}

static void test_player_contact_bounce_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0), *other=gaw_entity(16);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=20; p->raw[ENT_DIRECTION]=0;
    p->raw[ENT_PENDING_DAMAGE]=5; gaw_entity_set16(p,ENT_RELATED_PTR,gaw_entity_addr(other));
    other->raw[ENT_TYPE]=16; other->raw[ENT_FLAGS]=0x12; other->raw[ENT_ATTACK]=1;
    gaw_entity_set16(other,ENT_DELTA0,0x0100);
    gaw_ram_write8(0xC0F2,0); /* bank-12 threshold[0] = $28 */
    gaw_player_handler(p);
    assert(p->raw[ENT_PENDING_DAMAGE]==0);
    assert(gaw_entity_get16(other,ENT_DELTA0)==0xFF00);
    assert(other->raw[ENT_MOTION_PHASE]==0x0A);
    assert((other->raw[ENT_FLAGS]&0x02u)==0);
    assert(gaw_ram_read8(0xDE06)==0x98);
}

static void test_player_contact_realign_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0), *other=gaw_entity(16);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=20;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40; p->raw[ENT_PENDING_DAMAGE]=3;
    gaw_entity_set16(p,ENT_RELATED_PTR,gaw_entity_addr(other));
    other->raw[ENT_TYPE]=16; other->raw[ENT_DIRECTION]=0; other->raw[0x11]=0x50;
    gaw_player_handler(p);
    assert(p->raw[0x11]==0x38); /* snapped to $40 then pushed -8 */
    assert(p->raw[0x13]==0x40);
    assert(p->raw[ENT_STATE]==0);
    assert(p->raw[ENT_HIT_FLASH_TIMER]==0x30);
}

static void test_player_grid_transition_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=7; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40; p->raw[ENT_DIRECTION]=0;
    gaw_ram_write8(0xC090,1); gaw_ram_write8(0xC0EC,1); gaw_ram_write8(0xC0DD,40);
    /* C052 (cache offset 10) gets B5 from D7CD and triggers $2F18. */
    gaw_ram_write8(0xD7CD,0xB5);
    gaw_ram_write16le(0xC034,0xD000);
    for (unsigned i=0;i<8;++i) gaw_ram_write8((uint16_t)(0xC918+i),(uint8_t)(0xA0+i));
    gaw_player_handler(p);
    assert(p->raw[0x11]==0x38 && p->raw[0x13]==0x40);
    assert(gaw_ram_read8(0xC0DD)==10);
    assert(gaw_ram_read8(0xDC34)==3);
    assert(gaw_ram_read16le(0xC034)==0xD005);
    assert(gaw_ram_read8(0xD000)==2 && gaw_ram_read8(0xD001)==2 && gaw_ram_read8(0xD002)==2);
}


static void test_player_mode3_action_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0), *clone=gaw_entity(1);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    /* In table $2544 record 3, both center tiles in the $11/$12/... list -> mode 3. */
    gaw_ram_write8(0xD7CD,0x11); gaw_ram_write8(0xD7CF,0x11);
    gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    gaw_player_handler(p);
    assert(gaw_ram_read8(RAM_PLAYER_ENV_MODE)==3);
    assert(clone->raw[ENT_TYPE]==5 && clone->raw[ENT_STATE]==0);
    assert(clone->raw[0x11]==p->raw[0x11] && clone->raw[0x13]==p->raw[0x13]);
    assert(gaw_ram_read8(0xDE06)==0xAA);
}



static void test_world_progress_bit_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0011);
    gaw_ram_write8(0xC040,0);
    assert(!gaw_world_progress_test_and_set());
    assert(gaw_ram_read8(0xC111)==0x01);
    assert(gaw_world_progress_test_and_set());

    gaw_ram_write16le(0xC0BB,0x0033);
    gaw_ram_write8(0xC040,1);
    assert(!gaw_world_progress_test_and_set());
    assert(gaw_ram_read8(0xC133)==0x02);
}

static void test_world_event_record_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0009);
    assert(gaw_world_progress_load_event_record());
    assert(gaw_ram_read8(0xC06E)==0x2A);
    assert(gaw_ram_read8(0xC06F)==0x31);
    assert(gaw_ram_read8(0xC070)==0x01);

    gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0110);
    assert(gaw_world_progress_load_event_record());
    assert(gaw_ram_read8(0xC06E)==0x28);
    assert(gaw_ram_read8(0xC06F)==0x28);
    assert(gaw_ram_read8(0xC070)==0x0A);
}

static void test_world_patch16_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(0xC034,0xD000);
    gaw_ram_write8(0xC06E,0x22);
    for (unsigned c=0;c<0x100;++c) gaw_ram_write8((uint16_t)(0xDC00u+c),0xEE);
    gaw_world_progress_apply_patch(16,0x44);
    assert(gaw_ram_read8(0xDC44)==0 && gaw_ram_read8(0xDC45)==0);
    assert(gaw_ram_read8(0xDC54)==0 && gaw_ram_read8(0xDC55)==0);
    assert(gaw_ram_read8(0xDC22)==0x4D);
    assert(gaw_ram_read16le(0xC034)==0xD019); /* five queued metatile writes */
}

static void test_world_restore_persistent_patch_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0009); /* -> 2A,31,patch 1 */
    gaw_ram_write8(0xC040,0);
    gaw_ram_write8(0xC109,0x01); /* already unlocked */
    gaw_ram_write16le(0xC034,0xD000);
    gaw_world_progress_restore_for_current_cell();
    assert(gaw_ram_read8(0xC06E)==0x2A && gaw_ram_read8(0xC06F)==0x31 && gaw_ram_read8(0xC070)==1);
    assert(gaw_ram_read8(0xDC2A)==0x31); /* patch type 1 uses target value at trigger cell */
    assert(gaw_ram_read8(0xDD00)==0);
}

static void test_player_world_action_unlock_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=5; p->raw[ENT_HP]=10;
    p->raw[ENT_DIRECTION]=0; p->raw[ENT_ANIM_TICK]=6;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write16le(RAM_WORLD_CELL_ID,0x0011);
    gaw_ram_write8(0xC06E,0x32); /* first action target for dir0/quadrant0 */
    gaw_ram_write8(0xC06F,0x55);
    gaw_ram_write8(0xC070,0x04); /* patch: tile 04 at target */
    gaw_ram_write8(0xDC32,0x80); /* $3620 record 0 -> 17 */
    gaw_ram_write8(0xDC42,0xEE); /* do not trigger record's optional second write */
    gaw_ram_write16le(0xC034,0xD000);
    gaw_player_handler(p);
    assert(gaw_ram_read8(0xDC32)==0x17);
    assert(gaw_ram_read8(0xC111)&0x01);
    assert(gaw_ram_read8(0xDC55)==0x04);
    assert(gaw_ram_read8(0xDE08)==0xA8);
}



static void test_player_actions_4_5_6_native(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    GawEntity *p=gaw_entity(0), *slot1=gaw_entity(1);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10;
    p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write8(0xC0DF,4); gaw_ram_write8(0xC0DB,20); gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    gaw_player_handler(p);
    assert(slot1->raw[ENT_TYPE]==3 && slot1->raw[ENT_STATE]==0);
    assert(gaw_ram_read8(0xC0C6)==1 && gaw_ram_read8(0xC0DB)==12);
    assert(gaw_ram_read8(0xDE06)==0x92);

    memset(gaw_ram,0,sizeof gaw_ram); p=gaw_entity(0); slot1=gaw_entity(1);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10; p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write8(0xC0DF,5); gaw_ram_write8(0xC0DB,20); gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    gaw_player_handler(p);
    assert(slot1->raw[ENT_TYPE]==4 && slot1->raw[ENT_STATE]==0);
    assert(gaw_ram_read8(0xC0DB)==12 && gaw_ram_read8(0xDE06)==0x93);

    memset(gaw_ram,0,sizeof gaw_ram); p=gaw_entity(0);
    p->raw[ENT_TYPE]=2; p->raw[ENT_STATE]=1; p->raw[ENT_HP]=10; p->raw[0x11]=0x40; p->raw[0x13]=0x40;
    gaw_ram_write8(0xC0DF,6); gaw_ram_write8(0xC0DB,40); gaw_ram_write8(0xC0E6,7); gaw_ram_write8(RAM_INPUT_PRESSED,0x20);
    gaw_player_handler(p);
    assert(gaw_ram_read8(0xC0DB)==8 && gaw_ram_read8(0xC090)==7);
    assert(p->raw[ENT_STATE]==7 && gaw_ram_read8(0xDE06)==0x94);
}

int main(void) {
    test_input_edges();
    test_pause_nmi();
    test_world_table();
    test_entity_core();
    test_damage_saturates();
    test_gameplay_init_and_state();
    test_gameplay_state_transitions();
    test_collision_player_pickup();
    test_collision_damage();
    test_pickup_reward_native();
    test_enemy_init_native();
    test_enemy_cull_native();
    test_player_walk_native();
    test_player_collision_deflection_native();
    test_player_action_animation_native();
    test_player_heal_native();
    test_player_death_states_native();
    test_player_full_entity_pass_native();
    test_player_environment_native();
    test_player_map_mutation_38ac_native();
    test_player_contact_bounce_native();
    test_player_contact_realign_native();
    test_player_grid_transition_native();
    test_player_mode3_action_native();
    test_world_progress_bit_native();
    test_world_event_record_native();
    test_world_patch16_native();
    test_world_restore_persistent_patch_native();
    test_player_world_action_unlock_native();
    test_player_actions_4_5_6_native();
    puts("phase7 tests: OK");
    return 0;
}
