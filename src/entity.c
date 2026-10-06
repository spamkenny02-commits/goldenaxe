#include <stddef.h>
#include <string.h>
#include "include/gaw_entity.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_tables.h"

_Static_assert(sizeof(GawEntity) == GAW_ENTITY_SIZE, "Entity record must remain 0x30 bytes");

GawEntity *gaw_entity(unsigned index) {
    if (index >= GAW_ENTITY_COUNT) return NULL;
    return (GawEntity *)(void *)gaw_ram_ptr((uint16_t)(RAM_ENTITIES + index * GAW_ENTITY_SIZE));
}

uint16_t gaw_entity_addr(const GawEntity *e) {
    ptrdiff_t off = (const uint8_t *)(const void *)e - gaw_ram;
    return (uint16_t)(GAW_RAM_BASE + off);
}

void gaw_entity_clear(GawEntity *e) {
    memset(e->raw, 0, GAW_ENTITY_SIZE);
}

uint16_t gaw_entity_get16(const GawEntity *e, unsigned off) {
    return (uint16_t)e->raw[off] | ((uint16_t)e->raw[off + 1] << 8);
}

void gaw_entity_set16(GawEntity *e, unsigned off, uint16_t value) {
    e->raw[off] = (uint8_t)value;
    e->raw[off + 1] = (uint8_t)(value >> 8);
}

static GawEntity *entity_from_sms_pointer(uint16_t addr) {
    if (addr < RAM_ENTITIES || addr >= RAM_ENTITIES + GAW_ENTITY_COUNT * GAW_ENTITY_SIZE)
        return NULL;
    return (GawEntity *)(void *)gaw_ram_ptr(addr);
}

static void dispatch_entity_handler(GawEntity *e) {
    uint8_t type = e->raw[ENT_TYPE];
    if (type == 0 || type > 127) return;
    (void)gaw_entity_native_handler(e,type);
}

static void update_motion_accumulators(GawEntity *e) {
    uint8_t a = (uint8_t)(e->raw[ENT_MOTION_PHASE] - 1u);
    if ((a & 0x80u) != 0) return; /* JP M,$271B */

    uint16_t de = (uint16_t)(gaw_entity_get16(e, ENT_DELTA0) +
                             gaw_entity_get16(e, ENT_ACCUM0));
    uint16_t hl = (uint16_t)(gaw_entity_get16(e, ENT_DELTA1) +
                             gaw_entity_get16(e, ENT_ACCUM1));

    if (a == 0) {
        /* $270A/$270B zero only the low bytes (L and E). */
        hl &= 0xFF00u;
        de &= 0xFF00u;
    }
    e->raw[ENT_MOTION_PHASE] = a;
    gaw_entity_set16(e, ENT_ACCUM1, hl);
    gaw_entity_set16(e, ENT_ACCUM0, de);
}

static void update_animation(GawEntity *e) {
    if (e->raw[ENT_ANIM_FRAMES] == 0) return;

    uint8_t tick = (uint8_t)(e->raw[ENT_ANIM_TICK] + 1u);
    if (tick >= e->raw[ENT_ANIM_DELAY]) tick = 0;
    e->raw[ENT_ANIM_TICK] = tick;
    if (tick != 0) return;

    uint8_t frame = (uint8_t)(e->raw[ENT_ANIM_FRAME] + 1u);
    if (frame == e->raw[ENT_ANIM_FRAMES]) frame = 0;
    e->raw[ENT_ANIM_FRAME] = frame;
}

static void update_hit_flash(GawEntity *e) {
    uint8_t a = (uint8_t)(e->raw[ENT_HIT_FLASH_TIMER] - 1u);
    if ((a & 0x80u) != 0) return;
    e->raw[ENT_HIT_FLASH_TIMER] = a;
    e->raw[ENT_FLAGS] |= 0x01u;
    if (a & 0x02u) e->raw[ENT_FLAGS] &= (uint8_t)~0x01u;
}

void gaw_entity_apply_pending_damage(GawEntity *e) {
    uint8_t damage = e->raw[ENT_PENDING_DAMAGE];
    if (damage == 0) return;

    GawEntity *related = entity_from_sms_pointer(gaw_entity_get16(e, ENT_RELATED_PTR));
    e->raw[ENT_PENDING_DAMAGE] = 0;

    /* $2768-$282F is translated until the final 4-way collision response.
       The four response handlers remain legacy hooks for now. */
    if (e->raw[ENT_FLAGS] & 0x40u) {
        e->raw[ENT_HP] = (damage > e->raw[ENT_HP]) ? 0 : (uint8_t)(e->raw[ENT_HP] - damage);
        if (e->raw[ENT_HP] == 0) {
            e->raw[ENT_TYPE] = 0x07;
            e->raw[ENT_COOLDOWN] = 0;
            e->raw[ENT_STATE] = 0;
            gaw_entity_set16(e, ENT_DELTA1, 0);
            gaw_entity_set16(e, ENT_DELTA0, 0);
            gaw_platform_audio_command(0x9E);
            return;
        }
    } else if (e->raw[ENT_FLAGS] & 0x20u) {
        if (e->raw[ENT_DEFENSE] == 0 && related && related->raw[ENT_TYPE] == 0x04) {
            e->raw[ENT_COOLDOWN] = 0xFF;
            return;
        }
        e->raw[ENT_HP] = (damage > e->raw[ENT_HP]) ? 0 : (uint8_t)(e->raw[ENT_HP] - damage);
        if (e->raw[ENT_HP] == 0) {
            e->raw[ENT_SAVED_TYPE] = e->raw[ENT_TYPE];
            e->raw[ENT_TYPE] = 0x01;
            e->raw[ENT_COOLDOWN] = 0;
            e->raw[ENT_STATE] = 0;
            gaw_entity_set16(e, ENT_DELTA1, 0);
            gaw_entity_set16(e, ENT_DELTA0, 0);
            gaw_platform_audio_command(0xA0);
            return;
        }
    } else {
        /* Original only applies this branch to entity slot 0. */
        if (gaw_ram_read8(RAM_ENTITY_SLOT_INDEX) != 0) return;
        e->raw[ENT_HP] = (damage > e->raw[ENT_HP]) ? 0 : (uint8_t)(e->raw[ENT_HP] - damage);
        return;
    }

    gaw_platform_audio_command(0x9C);
    e->raw[ENT_HIT_FLASH_TIMER] = 0x20;

    if ((e->raw[ENT_FLAGS] & 0x08u) && related) {
        uint8_t variant = related->raw[ENT_DIRECTION]&3u;
        /* $2838/$2863/$2890/$28B8: snap to the 8-pixel grid and try an
           8-pixel recoil step when the map descriptor is not blocked. */
        if (variant < 2u) {
            e->raw[0x13]=(uint8_t)((e->raw[0x13]+4u)&0xF8u);
            e->raw[0x11]=(uint8_t)((e->raw[0x11]+(variant?7u:0u))&0xF8u);
            if ((!variant && e->raw[0x11]>=0x19u) || (variant && e->raw[0x11]<0x88u)) {
                int8_t xo=variant?-8:-16; int8_t yo=variant?0:-8;
                uint8_t x=(uint8_t)(e->raw[0x11]+(uint8_t)xo), y=(uint8_t)(e->raw[0x13]+(uint8_t)yo);
                uint16_t off=(uint16_t)(((uint16_t)(x&0xF8u)<<3)+(((uint8_t)(y>>2))&0x3Eu));
                uint8_t hi=gaw_ram_read8((uint16_t)(0xD601u+off));
                uint8_t hi2=gaw_ram_read8((uint16_t)(0xD603u+off));
                if (((uint8_t)(hi|hi2)&0xA0u)==0) e->raw[0x11]=(uint8_t)(e->raw[0x11]+(variant?8u:0xF8u));
            }
        } else {
            e->raw[0x11]=(uint8_t)((e->raw[0x11]+4u)&0xF8u);
            e->raw[0x13]=(uint8_t)((e->raw[0x13]+(variant==3u?7u:0u))&0xF8u);
            if ((variant==2u && e->raw[0x13]>=0x19u) || (variant==3u && e->raw[0x13]<0xE8u)) {
                int8_t yo=variant==2u?-16:8;
                uint8_t x=(uint8_t)(e->raw[0x11]-8u), y=(uint8_t)(e->raw[0x13]+(uint8_t)yo);
                uint16_t off=(uint16_t)(((uint16_t)(x&0xF8u)<<3)+(((uint8_t)(y>>2))&0x3Eu));
                uint8_t hi=gaw_ram_read8((uint16_t)(0xD601u+off));
                if ((hi&0xA0u)==0) e->raw[0x13]=(uint8_t)(e->raw[0x13]+(variant==2u?0xF8u:8u));
            }
        }
        e->raw[ENT_ACCUM1] = 0; /* $2819: only low byte of +$12 */
        gaw_entity_set16(e, ENT_DELTA1, 0);
        e->raw[ENT_ACCUM0] = 0; /* $2823 leaves +$11 unchanged */
        gaw_entity_set16(e, ENT_DELTA0, 0);
        e->raw[ENT_MOTION_PHASE] = 0;
    }
}


static int checked_add_negative_offset(uint8_t pos, uint8_t encoded, uint8_t *out) {
    int v = (int)pos + (int)(int8_t)encoded;
    if (v < 0 || v > 255) return 0;
    *out = (uint8_t)v;
    return 1;
}

static int checked_add_extent(uint8_t pos, uint8_t extent, uint8_t *out) {
    unsigned v = (unsigned)pos + extent;
    if (v > 255u) return 0;
    *out = (uint8_t)v;
    return 1;
}

static int collision_axis(uint8_t cand_pos, uint8_t cand_off, uint8_t cand_extent,
                          uint8_t cur_min, uint8_t cur_max) {
    uint8_t lo, hi;
    if (!checked_add_negative_offset(cand_pos, cand_off, &lo)) return 0;
    if (lo >= cur_max) return 0;
    if (!checked_add_extent(lo, cand_extent, &hi)) return 0;
    if (hi < cur_min) return 0;
    return 1;
}

void gaw_entity_collision_scan(GawEntity *e) {
    /* Exact C-visible reconstruction of $2346-$2403. The original spreads
       collision work over alternate frames using frame_counter XOR slot. */
    uint8_t slot = gaw_ram_read8(RAM_ENTITY_SLOT_INDEX);
    if (((gaw_ram_read8(RAM_FRAME_COUNTER) ^ slot) & 1u) != 0) return;
    if (e->raw[ENT_HIT_FLASH_TIMER] != 0) return;
    if ((e->raw[ENT_FLAGS] & 0x02u) == 0) return;

    uint8_t source_box = e->raw[ENT_HITBOX_SOURCE];
    if (source_box == 0 || source_box >= 48) return;
    const uint8_t *src = gaw_hitboxes[source_box];

    uint8_t cur_y0 = (uint8_t)(e->raw[0x13] + src[0]);
    uint8_t cur_y1 = (uint8_t)(cur_y0 + src[1]);
    uint8_t cur_x0 = (uint8_t)(e->raw[0x11] + src[2]);
    uint8_t cur_x1 = (uint8_t)(cur_x0 + src[3]);

    unsigned first, count;
    if (slot == 0) { first=9; count=23; }
    else if (slot <= 8) { first=9; count=7; }
    else if (slot <= 15) { first=0; count=1; }
    else { first=0; count=9; }

    for (unsigned j=0; j<count; ++j) {
        GawEntity *other = gaw_entity(first+j);
        if (!other || other->raw[ENT_TYPE] == 0 || other->raw[ENT_COOLDOWN] != 0) continue;
        if ((other->raw[ENT_FLAGS] & 0x02u) == 0) continue;
        uint8_t target_box = other->raw[ENT_HITBOX_TARGET];
        if (target_box == 0 || target_box >= 48) continue;
        const uint8_t *dst = gaw_hitboxes[target_box];

        if (!collision_axis(other->raw[0x13], dst[0], dst[1], cur_y0, cur_y1)) continue;
        if (!collision_axis(other->raw[0x11], dst[2], dst[3], cur_x0, cur_x1)) continue;

        if (!(e->raw[ENT_TYPE] == 2 && other->raw[ENT_TYPE] < 0x10)) {
            uint8_t attack = other->raw[ENT_ATTACK];
            uint8_t defense = e->raw[ENT_DEFENSE];
            uint8_t damage = attack > defense ? (uint8_t)(attack-defense) : 2u;
            e->raw[ENT_PENDING_DAMAGE] = (uint8_t)(e->raw[ENT_PENDING_DAMAGE] + damage);
        }
        gaw_entity_set16(e, ENT_RELATED_PTR, gaw_entity_addr(other));
        other->raw[ENT_FLAGS] |= 0x04u;
        return; /* $23D6-$2403 returns after the first collision. */
    }
}

void gaw_entities_update_all(void) {
    gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, 0);
    gaw_ram_write8(RAM_ACTIVE_ENTITY_COUNT, 0);

    for (unsigned i = 0; i < GAW_ENTITY_COUNT; ++i) {
        GawEntity *e = gaw_entity(i);
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, (uint8_t)i);
        if (e->raw[ENT_TYPE] == 0) continue;

        gaw_entity_collision_scan(e);
        gaw_ram_write8(RAM_ACTIVE_ENTITY_COUNT,
                       (uint8_t)(gaw_ram_read8(RAM_ACTIVE_ENTITY_COUNT) + 1u));

        if (e->raw[ENT_COOLDOWN] != 0) {
            --e->raw[ENT_COOLDOWN];
        } else {
            dispatch_entity_handler(e);
            update_motion_accumulators(e);
            update_animation(e);
        }

        update_hit_flash(e);
        gaw_entity_apply_pending_damage(e);
    }
    /* Z80 increments C046 after the last slot, leaving exactly $20. */
    gaw_ram_write8(RAM_ENTITY_SLOT_INDEX, GAW_ENTITY_COUNT);
}
