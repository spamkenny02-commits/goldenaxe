#include <string.h>
#include "include/gaw_entity.h"
#include "include/gaw_ram.h"
#include "include/gaw_tables.h"
#include "include/gaw_player.h"
#include "include/gaw_platform.h"
#include "include/gaw_world_progress.h"

#define PLAYER_STATE_ADDR 0xC301u
#define PLAYER_X_ADDR     0xC311u
#define PLAYER_Y_ADDR     0xC313u

static void pickup_init(GawEntity *e, uint8_t gfx, uint16_t data_ptr) {
    e->raw[ENT_GFX_ID] = gfx;
    e->raw[0x08] = (uint8_t)data_ptr;
    e->raw[0x09] = (uint8_t)(data_ptr >> 8);
    e->raw[ENT_ANIM_DELAY] = 0;
    e->raw[ENT_ANIM_FRAMES] = 0;
    e->raw[ENT_ANIM_FRAME] = 0;
    e->raw[ENT_PENDING_DAMAGE] = 0;
    e->raw[ENT_FLAGS] = 0x01;
    e->raw[ENT_STATE] = 0x02;
}

static void pickup_common_state(GawEntity *e, uint8_t gfx, uint16_t data_ptr, int persistent) {
    switch (e->raw[ENT_STATE]) {
        case 0:
            pickup_init(e, gfx, data_ptr);
            break;
        case 2:
            if (gaw_ram_read8(PLAYER_STATE_ADDR) == 1) {
                e->raw[ENT_FLAGS] |= 0x02u;
                if (!persistent) e->raw[ENT_ANIM_TICK] = 0xF0;
                e->raw[ENT_STATE] = 4;
            }
            break;
        case 4:
            if (persistent) break;
            e->raw[ENT_ANIM_TICK] = (uint8_t)(e->raw[ENT_ANIM_TICK] - 1u);
            if (e->raw[ENT_ANIM_TICK] == 0) {
                e->raw[ENT_HIT_FLASH_TIMER] = 0x78;
                e->raw[ENT_STATE] = 6;
            }
            break;
        case 6:
            if (e->raw[ENT_HIT_FLASH_TIMER] == 0) gaw_entity_clear(e);
            break;
        default:
            break;
    }
}

/* $2ADD: returns true exactly when the entity was consumed by collision/damage. */
static int pickup_consume_if_touched(GawEntity *e) {
    if (e->raw[ENT_PENDING_DAMAGE] == 0 && (e->raw[ENT_FLAGS] & 0x04u) == 0)
        return 0;
    gaw_entity_clear(e);
    gaw_ram_write8(0xDE08, 0x96);
    return 1;
}

static uint8_t sat_add_u8(uint8_t a, uint8_t b) {
    unsigned v = (unsigned)a + b;
    return (uint8_t)(v > 0xFFu ? 0xFFu : v);
}

static void pickup_handler(GawEntity *e, uint8_t type) {
    switch (type) {
        case 8: pickup_common_state(e, 0x92, 0x84CE, 0); break;
        case 9: pickup_common_state(e, 0x94, 0x84CE, 0); break;
        case 10: pickup_common_state(e, 0xAA, 0x84E1, 0); break;
        case 14: pickup_common_state(e, 0x96, 0x84CE, 1); break;
        default: return;
    }
    if (!pickup_consume_if_touched(e)) return;

    switch (type) {
        case 8:
            gaw_ram_write8(0xC0DD, sat_add_u8(gaw_ram_read8(0xC0DD), 1));
            break;
        case 9:
            gaw_ram_write8(0xC0DD, sat_add_u8(gaw_ram_read8(0xC0DD), 5));
            break;
        case 10: {
            uint8_t cap = gaw_ram_read8(0xC0DA);
            uint8_t hp = gaw_ram_read8(0xC318);
            unsigned v = (unsigned)hp + 8u;
            gaw_ram_write8(0xC318, (uint8_t)(v < cap ? v : cap));
            break;
        }
        case 14: {
            uint8_t v = gaw_ram_read8(0xC0DE);
            if (v < 0x63) ++v;
            gaw_ram_write8(0xC0DE, v);
            break;
        }
    }
}

static void entity_cull_common(GawEntity *e) {
    uint8_t x=e->raw[0x11], y=e->raw[0x13];
    int kill;
    if (gaw_ram_read8(0xC0BA) == 1)
        kill = x < 0x20 || x >= 0x88 || y < 0x20 || y >= 0xE0 || e->raw[ENT_MOTION_PHASE] == 0;
    else
        kill = x < 0x08 || x >= 0x98 || y < 0x08 || y >= 0xF8 || e->raw[ENT_MOTION_PHASE] == 0;
    if (kill) gaw_entity_clear(e);
}

static int enemy_init_standard(GawEntity *e, uint8_t type, const uint8_t *cfg) {
    unsigned dir = e->raw[ENT_DIRECTION];
    if (dir > 3) return 0; /* original data uses 0..3; invalid records stay untouched */
    e->raw[0x08] = cfg[0];
    e->raw[0x09] = cfg[1];
    e->raw[ENT_ATTACK] = cfg[2];
    e->raw[0x11] = (uint8_t)(e->raw[0x11] + cfg[3]);
    e->raw[ENT_ANIM_FRAMES] = cfg[4];
    e->raw[ENT_ANIM_DELAY] = cfg[5];
    unsigned p = 6u + dir * 4u;
    e->raw[0x14]=cfg[p]; e->raw[0x15]=cfg[p+1];
    e->raw[0x16]=cfg[p+2]; e->raw[0x17]=cfg[p+3];
    e->raw[ENT_STATE] = 2;
    e->raw[ENT_MOTION_PHASE] = 0x80;
    e->raw[ENT_FLAGS] = 0x13;
    (void)type;
    return 1;
}

static void enemy_init_toward_player(GawEntity *e, const uint8_t *cfg) {
    e->raw[0x08] = cfg[0];
    e->raw[0x09] = cfg[1];
    e->raw[ENT_ATTACK] = cfg[2];
    e->raw[0x11] = (uint8_t)(e->raw[0x11] + cfg[3]);
    e->raw[ENT_ANIM_FRAMES] = cfg[4];
    e->raw[ENT_ANIM_DELAY] = cfg[5];

    uint8_t c = 2;
    int dy = (int)gaw_ram_read8(PLAYER_Y_ADDR) - (int)e->raw[0x13];
    if (dy < 0) { dy = -dy; c |= 4u; }
    int dx = (int)gaw_ram_read8(PLAYER_X_ADDR) - (int)e->raw[0x11];
    if (dx < 0) { dx = -dx; c &= (uint8_t)~2u; }
    if (dx < dy) ++c;

    e->raw[ENT_DIRECTION] = gaw_direction_codes[c];
    unsigned p = 6u + (unsigned)c * 4u;
    /* $3F3B-$3F4B writes Y velocity first, then X velocity. */
    e->raw[0x16]=cfg[p]; e->raw[0x17]=cfg[p+1];
    e->raw[0x14]=cfg[p+2]; e->raw[0x15]=cfg[p+3];
    e->raw[ENT_STATE] = 2;
    e->raw[ENT_MOTION_PHASE] = 0x60;
    e->raw[ENT_FLAGS] = 0x13;
}

static int enemy_handler(GawEntity *e, uint8_t type) {
    const uint8_t *cfg = (type == 25 && (gaw_ram_read8(RAM_FRAME_COUNTER) & 1u))
                       ? gaw_enemy_config25_alt : gaw_enemy_configs[type];
    if (e->raw[ENT_STATE] != 0) {
        entity_cull_common(e);
        if (type == 18) {
            uint8_t t=(uint8_t)(e->raw[ENT_ANIM_TICK]+1u);
            if (t >= 2) t=0;
            e->raw[ENT_ANIM_TICK]=t;
            if (t==0) {
                uint8_t f=(uint8_t)(e->raw[ENT_ANIM_FRAME]+1u);
                if (f >= 4) f=1;
                e->raw[ENT_ANIM_FRAME]=f;
            }
        }
        return 1;
    }

    if (type==19 || type==20 || type==21 || type==30) {
        enemy_init_toward_player(e,cfg);
        return 1;
    }
    return enemy_init_standard(e,type,cfg);
}


/* Phase 9 ROM-derived data. */
static const uint8_t death_saved_types[32] = {
#include "death_saved_types.inc"
};
static const uint8_t death_drop_classes[32] = {
#include "death_drop_classes.inc"
};
static const uint8_t death_drop_rules[32] = {
#include "death_drop_rules.inc"
};
static const uint8_t action_type3_velocity[8] = {
#include "action_type3_velocity.inc"
};
static const uint8_t action_type3_offset[8] = {
#include "action_type3_offset.inc"
};
static const uint8_t action_type4_velocity[8] = {
#include "action_type4_velocity.inc"
};
static const uint8_t action_type4_offsets_a[8] = {
#include "action_type4_offsets_a.inc"
};
static const uint8_t action_type4_offsets_b[8] = {
#include "action_type4_offsets_b.inc"
};
static const uint8_t action_type4_tiles_interior[8] = {
#include "action_type4_tiles_interior.inc"
};
static const uint8_t action_type4_tiles_world[20] = {
#include "action_type4_tiles_world.inc"
};
static const uint8_t action_type4_tiles_alt[8] = {
#include "action_type4_tiles_alt.inc"
};
static const uint8_t action_type5_velocity[8] = {
#include "action_type5_velocity.inc"
};
static const uint8_t action_type5_attack[32] = {
#include "action_type5_attack.inc"
};
static const uint8_t entity28_config[38] = {
#include "entity28_config.inc"
};
static const uint8_t entity29_launch[10] = {
#include "entity29_launch.inc"
};
static const uint8_t entity31_config[38] = {
#include "entity31_config.inc"
};
static const uint8_t entity32_spawn_types[3] = {
#include "entity32_spawn_types.inc"
};
static const uint8_t entity32_motion[17] = {
#include "entity32_motion.inc"
};
static const uint8_t entity_spawn_tiles16[16] = {
#include "entity_spawn_tiles16.inc"
};
static const uint8_t entity_fixed_position_data[0x274] = {
#include "entity_fixed_position_data.inc"
};
static const uint8_t sine_table[256] = {
#include "sine_table.inc"
};
static const uint8_t entity35_target_offsets[6] = {
#include "entity35_target_offsets.inc"
};
static const uint8_t entity38_variant[3] = {
#include "entity38_variant.inc"
};
static const uint8_t entity38_motion_fast[17] = {
#include "entity38_motion_fast.inc"
};
static const uint8_t entity42_motion[17] = {
#include "entity42_motion.inc"
};
static const uint8_t entity49_records[64] = {
#include "entity49_records.inc"
};
static const uint8_t entity50_records[64] = {
#include "entity50_records.inc"
};
static const uint8_t entity51_probe[12] = {
#include "entity51_probe.inc"
};
static const uint8_t entity51_ballistic[16] = {
#include "entity51_ballistic.inc"
};
static const uint8_t entity53_motion[17] = {
#include "entity53_motion.inc"
};
static const uint8_t entity58_charge[17] = {
#include "entity58_charge.inc"
};

static uint16_t u16le_at(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}
static void set_word_bytes(GawEntity *e, unsigned off, uint16_t v) {
    e->raw[off]=(uint8_t)v; e->raw[off+1]=(uint8_t)(v>>8);
}

/* $04E1, except the physical Z80 refresh register R is supplied by the
   platform. The RAM LFSR state and final XOR are preserved exactly. */
static uint8_t original_random_byte(void) {
    uint16_t hl=gaw_ram_read16le(0xC028);
    uint8_t h=(uint8_t)(hl>>8), l=(uint8_t)hl, a=h;
#define RRCA8(v) (uint8_t)(((v)>>1)|((v)<<7))
    a=RRCA8(a); a=RRCA8(a); a^=h; a=RRCA8(a); a^=l;
    a=RRCA8(a); a=RRCA8(a); a=RRCA8(a); a=RRCA8(a); a^=l;
    uint8_t carry=(uint8_t)(a&1u); /* carry produced by the following RRA */
    hl=(uint16_t)((uint16_t)(hl<<1)+carry);
    if (hl==0) hl=0x733C;
    gaw_ram_write16le(0xC028,hl);
#undef RRCA8
    return (uint8_t)(gaw_platform_entropy8() ^ (uint8_t)hl);
}

static uint16_t entity_map_descriptor(const GawEntity *e, int8_t yoff, int8_t xoff) {
    uint8_t x=(uint8_t)(e->raw[0x11]+(uint8_t)xoff);
    uint8_t y=(uint8_t)(e->raw[0x13]+(uint8_t)yoff);
    uint16_t off=(uint16_t)((uint16_t)(x&0xF8u)<<3);
    off=(uint16_t)(off+(uint16_t)(((uint8_t)(y>>2))&0x3Eu));
    return gaw_ram_read16le((uint16_t)(0xD600u+off));
}

static void set_directional_high_velocity(GawEntity *e, const uint8_t table[8]) {
    unsigned d=e->raw[ENT_DIRECTION]&3u;
    uint16_t w=u16le_at(table+d*2u);
    e->raw[ENT_DELTA0+1]=(uint8_t)w;
    e->raw[ENT_DELTA1+1]=(uint8_t)(w>>8);
}

static uint8_t world_cell_from_entity_offset(const GawEntity *e, int8_t yoff, int8_t xoff) {
    uint8_t y=(uint8_t)(e->raw[0x13]+(uint8_t)yoff);
    uint8_t x=(uint8_t)(e->raw[0x11]+(uint8_t)xoff);
    return (uint8_t)((x&0xF0u)|((y&0xF0u)>>4));
}
static void action4_write_tile(uint8_t cell, uint8_t tile) {
    gaw_ram_write8((uint16_t)(0xDC00u+cell),tile);
    if (cell!=gaw_ram_read8(RAM_WORLD_EVENT_TRIGGER)) { gaw_ram_write8(0xDE06,0x9B); return; }
    gaw_world_commit_metatile(cell,tile);
    if (!gaw_world_progress_test_and_set()) { gaw_ram_write8(0xDE08,0xA8); gaw_world_progress_apply_loaded_patch(); }
}
static void action4_try_tile(GawEntity *e, int8_t yoff, int8_t xoff, const uint8_t *records, unsigned bytes) {
    uint8_t cell=world_cell_from_entity_offset(e,yoff,xoff);
    uint8_t old=gaw_ram_read8((uint16_t)(0xDC00u+cell));
    for (unsigned i=0;i+3<bytes;i+=4) {
        if (records[i]==0) return;
        if (old!=records[i]) continue;
        action4_write_tile(cell,records[i+1]);
        uint8_t below=(uint8_t)(cell+0x10u);
        if (gaw_ram_read8((uint16_t)(0xDC00u+below))==records[i+2]) action4_write_tile(below,records[i+3]);
        return;
    }
}
static void action4_world_side_effect(GawEntity *e) {
    unsigned d=e->raw[ENT_DIRECTION]&3u;
    const uint8_t *records; unsigned n;
    if (gaw_ram_read8(0xC0BA)!=0) { records=action_type4_tiles_interior; n=sizeof action_type4_tiles_interior; }
    else if (gaw_ram_read8(0xC0E5)==1) { records=action_type4_tiles_alt; n=sizeof action_type4_tiles_alt; }
    else { records=action_type4_tiles_world; n=sizeof action_type4_tiles_world; }
    uint16_t w=u16le_at(action_type4_offsets_a+d*2u);
    action4_try_tile(e,(int8_t)(w>>8),(int8_t)w,records,n);
    w=u16le_at(action_type4_offsets_b+d*2u);
    action4_try_tile(e,(int8_t)(w>>8),(int8_t)w,records,n);
}

/* Types 3, 4 and 5 are the short-lived entities cloned from Arthur by item
   actions. Their handlers are $393A/$3A27/$39CC. */
static int action_entity_handler(GawEntity *e, uint8_t type) {
    unsigned d=e->raw[ENT_DIRECTION]&3u;
    if (type==3) {
        if (e->raw[ENT_STATE]==0) {
            e->raw[ENT_FLAGS]=0x03;
            uint16_t ptr=(gaw_ram_read8(0xC0E4)==1)?0x8411u:0x8419u;
            e->raw[0x08]=(uint8_t)ptr; e->raw[0x09]=(uint8_t)(ptr>>8);
            e->raw[ENT_ANIM_FRAMES]=4; e->raw[ENT_ANIM_DELAY]=1;
            set_directional_high_velocity(e,action_type3_velocity);
            uint16_t off=u16le_at(action_type3_offset+d*2u);
            e->raw[0x11]=(uint8_t)(e->raw[0x11]+(uint8_t)off);
            e->raw[0x13]=(uint8_t)(e->raw[0x13]+(uint8_t)(off>>8));
            e->raw[ENT_STATE]=1;
            /* $398A falls directly into $398D. */
        }
        e->raw[ENT_MOTION_PHASE]=2;
        uint8_t dh=(uint8_t)(entity_map_descriptor(e,0,0)>>8);
        if ((dh&0xE0u)==0x80u || (dh&0xE0u)==0xA0u ||
            e->raw[0x13]>=0xF8u || e->raw[0x13]<0x08u ||
            (uint8_t)(e->raw[0x11]+8u)>=0xA8u) gaw_entity_clear(e);
        return 1;
    }
    if (type==4) {
        if (e->raw[ENT_STATE]==0) {
            e->raw[ENT_FLAGS]=0x03; e->raw[0x08]=0x61; e->raw[0x09]=0x84;
            e->raw[ENT_ANIM_FRAMES]=4; e->raw[ENT_ANIM_DELAY]=2;
            set_directional_high_velocity(e,action_type4_velocity); e->raw[ENT_STATE]=1;
        }
        e->raw[ENT_MOTION_PHASE]=2;
        if ((entity_map_descriptor(e,0,-8)&0x8000u)!=0 || e->raw[0x13]>=0xF8u || e->raw[0x13]<8u || (uint8_t)(e->raw[0x11]+8u)>=0xA9u) { gaw_entity_clear(e); return 1; }
        uint8_t q0=(uint8_t)gaw_ram_read16le(0xC034); action4_world_side_effect(e);
        if (gaw_ram_read8(0xC034)!=q0) gaw_entity_clear(e);
        return 1;
    }
    if (type==5) {
        if (e->raw[ENT_STATE]==0) {
            e->raw[0x08]=0x8D; e->raw[0x09]=0x3D;
            e->raw[ENT_ANIM_FRAMES]=2; e->raw[ENT_ANIM_DELAY]=1;
            uint8_t idx=gaw_ram_read8(0xC0E0);
            e->raw[ENT_ATTACK]=idx<sizeof action_type5_attack?action_type5_attack[idx]:0;
            set_directional_high_velocity(e,action_type5_velocity);
            e->raw[0x11]=(uint8_t)(e->raw[0x11]-2u);
            e->raw[ENT_STATE]=1; e->raw[ENT_MOTION_PHASE]=8;
            /* $3A12 falls directly into $3A16. */
        }
        if (e->raw[ENT_MOTION_PHASE]==0) { gaw_entity_clear(e); return 1; }
        if (e->raw[0x13]>=0xF8u || e->raw[0x13]<0x08u ||
            (uint8_t)(e->raw[0x11]+8u)>=0xA8u) gaw_entity_clear(e);
        return 1;
    }
    return 0;
}

static void pickup_lifecycle_after_init(GawEntity *e) {
    switch (e->raw[ENT_STATE]) {
        case 2:
            if (gaw_ram_read8(PLAYER_STATE_ADDR)==1) {
                e->raw[ENT_FLAGS]|=0x02u; e->raw[ENT_ANIM_TICK]=0xF0; e->raw[ENT_STATE]=4;
            }
            break;
        case 4:
            e->raw[ENT_ANIM_TICK]=(uint8_t)(e->raw[ENT_ANIM_TICK]-1u);
            if (e->raw[ENT_ANIM_TICK]==0) { e->raw[ENT_HIT_FLASH_TIMER]=0x78; e->raw[ENT_STATE]=6; }
            break;
        case 6:
            if (e->raw[ENT_HIT_FLASH_TIMER]==0) gaw_entity_clear(e);
            break;
        default: break;
    }
}

static int resource_pickup_handler(GawEntity *e, uint8_t type) {
    if (e->raw[ENT_STATE]==0) {
        uint8_t rid=(uint8_t)(0x10u+type); /* 11/12/13 -> $1B/$1C/$1D */
        uint8_t active=gaw_ram_read8(0xC0A3);
        if (active!=0 && active!=rid) { gaw_entity_clear(e); return 1; }
        if (active==0) { gaw_ram_write8(0xC0A3,rid); gaw_platform_entity_resource_load(rid); }
        pickup_init(e,0xBC,0x84E1);
    } else pickup_lifecycle_after_init(e);
    if (!pickup_consume_if_touched(e)) return 1;
    if (type==11) {
        uint8_t cap=gaw_ram_read8(0xC0DA), hp=gaw_ram_read8(0xC318);
        unsigned v=(unsigned)hp+0x18u; gaw_ram_write8(0xC318,(uint8_t)(v<cap?v:cap));
    } else if (type==12) {
        uint8_t cap=gaw_ram_read8(0xC0DC), v=gaw_ram_read8(0xC0DB);
        unsigned n=(unsigned)v+8u; gaw_ram_write8(0xC0DB,(uint8_t)(n<cap?n:cap));
    } else {
        for (unsigned i=16;i<32;++i) { GawEntity *x=gaw_entity(i); if (x->raw[ENT_TYPE]>=0x20) x->raw[ENT_COOLDOWN]=0xFF; }
    }
    return 1;
}

static int special_pickup15_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) {
        gaw_ram_write8(0xC0AE,0);
        static const uint8_t gfx_by_index[9]={0x85,0x83,0x87,0x89,0x82,0x88,0x86,0x84,0x8A};
        uint8_t idx=gaw_ram_read8(0xC037); uint8_t gfx=(idx>=1 && idx<=9)?gfx_by_index[idx-1u]:0x85;
        pickup_init(e,gfx,0x2ACD); e->raw[0x11]=0x1C; e->raw[0x13]=0x80;
    } else if (e->raw[ENT_STATE]==2) {
        if (gaw_ram_read8(PLAYER_STATE_ADDR)==1) { e->raw[ENT_FLAGS]|=0x02u; e->raw[ENT_STATE]=4; }
    }
    if (!pickup_consume_if_touched(e)) return 1;
    uint8_t idx=gaw_ram_read8(0xC037); gaw_ram_write8((uint16_t)(0xC0CEu+idx),0x80);
    static const uint8_t item_by_index[9]={0x24,0x22,0x26,0x28,0x21,0x27,0x25,0x23,0x29};
    uint8_t item=(idx>=1 && idx<=9)?item_by_index[idx-1u]:0x24;
    gaw_ram_write8(0xC0A3,item); (void)gaw_world_progress_test_and_set(); gaw_world_progress_apply_loaded_patch(); gaw_platform_entity_resource_load(item);
    uint8_t cap=gaw_ram_read8(0xC0DA); if ((uint8_t)(cap+8u)<0x81u) gaw_ram_write8(0xC0DA,(uint8_t)(cap+8u));
    gaw_ram_write8(0xC0DB,gaw_ram_read8(0xC0DC)); gaw_ram_write8(0xC318,gaw_ram_read8(0xC0DA));
    return 1;
}

/* Type 1 / $4AEE: normal enemy death animation and probabilistic drop. */
static int enemy_death_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) {
        e->raw[ENT_FLAGS]|=0x01u; e->raw[0x08]=0xCC; e->raw[0x09]=0x90;
        e->raw[ENT_ANIM_DELAY]=4; e->raw[ENT_ANIM_FRAMES]=5;
        e->raw[ENT_ANIM_FRAME]=0; e->raw[ENT_ANIM_TICK]=0; e->raw[ENT_STATE]=2;
        unsigned slot=(unsigned)((gaw_entity_addr(e)-RAM_ENTITIES)/GAW_ENTITY_SIZE);
        if (slot+1<GAW_ENTITY_COUNT && gaw_entity(slot+1)->raw[ENT_TYPE]==0x30) gaw_entity_clear(gaw_entity(slot+1));
        return 1;
    }
    if (e->raw[ENT_ANIM_FRAME]<4) return 1;
    uint8_t saved=e->raw[ENT_SAVED_TYPE];
    if (saved!=0) {
        uint8_t drop_class=2;
        if (gaw_ram_read8(0xC0BA)!=0) drop_class=gaw_ram_read8(0xC0BA);
        else for (unsigned i=0;i<32;++i) if (death_saved_types[i]==saved) { drop_class=death_drop_classes[i]; break; }
        if ((unsigned)drop_class+1u < sizeof death_drop_rules) {
            uint8_t rnd=original_random_byte();
            uint8_t threshold=death_drop_rules[drop_class];
            uint8_t spawn_type=death_drop_rules[drop_class+1u];
            if ((rnd&0x1Fu)<threshold && spawn_type!=0) {
                for (unsigned i=9;i<16;++i) {
                    GawEntity *p=gaw_entity(i); if (p->raw[ENT_TYPE]) continue;
                    p->raw[ENT_TYPE]=spawn_type; p->raw[ENT_STATE]=0; p->raw[ENT_FLAGS]=0;
                    p->raw[0x11]=e->raw[0x11]; p->raw[0x13]=e->raw[0x13]; break;
                }
            }
        }
    }
    gaw_entity_clear(e);
    gaw_ram_write8(0xC0A2,(uint8_t)(gaw_ram_read8(0xC0A2)-1u));
    return 1;
}

/* Type 7 / $4BA4: special/boss death sequence and explosion spawner. */
static int boss_death_handler(GawEntity *e) {
    uint8_t idx=gaw_ram_read8(0xC037);
    if (e->raw[ENT_STATE]==0) {
        if (idx>=0x0A) gaw_ram_write8(PLAYER_STATE_ADDR,0x0C);
        gaw_ram_write8((uint16_t)(0xC0CEu+idx),1);
        memset(gaw_ram_ptr(0xC780),0,0x180);
        e->raw[ENT_FLAGS]&=(uint8_t)~0x41u; e->raw[0x28]=0xB4; e->raw[ENT_STATE]=2;
        return 1;
    }
    if (e->raw[ENT_STATE]==2) {
        e->raw[0x28]=(uint8_t)(e->raw[0x28]-1u);
        if (e->raw[0x28]==0) { e->raw[ENT_STATE]=4; return 1; }
        if ((gaw_platform_entropy8()&3u)!=0) return 1;
        GawEntity *slot=NULL; for (unsigned i=24;i<32;++i) if (gaw_entity(i)->raw[ENT_TYPE]==0) { slot=gaw_entity(i); break; }
        if (!slot) return 1;
        uint8_t r=original_random_byte();
        uint8_t x=(uint8_t)((r&0x3Cu)+e->raw[0x11]-0x10u);
        if ((uint8_t)(x-0x18u)>=0x80u) return 1;
        uint8_t rot=(uint8_t)((r>>4)|(r<<4));
        uint8_t y=(uint8_t)((rot&0x3Cu)+e->raw[0x13]-0x20u);
        if ((uint8_t)(y-0x18u)>=0xD0u) return 1;
        slot->raw[0x11]=x; slot->raw[0x13]=y; slot->raw[ENT_TYPE]=1; slot->raw[ENT_STATE]=0; slot->raw[ENT_SAVED_TYPE]=0;
        return 1;
    }
    if (e->raw[ENT_STATE]==4) {
        gaw_ram_write8(0xDE08,0xB0); e->raw[ENT_STATE]=0; e->raw[ENT_TYPE]=0;
        if (idx<0x0A) e->raw[ENT_TYPE]=0x0F; else gaw_ram_write8(RAM_MAIN_STATE,0x0E);
        return 1;
    }
    return 1;
}

static void toward_player_motion_only(GawEntity *e, const uint8_t *motion) {
    uint8_t c=2; int dy=(int)gaw_ram_read8(PLAYER_Y_ADDR)-(int)e->raw[0x13];
    if (dy<0) { dy=-dy; c|=4u; }
    int dx=(int)gaw_ram_read8(PLAYER_X_ADDR)-(int)e->raw[0x11];
    if (dx<0) { dx=-dx; c&=(uint8_t)~2u; }
    if (dx<dy) ++c;
    e->raw[ENT_DIRECTION]=gaw_direction_codes[c];
    unsigned p=(unsigned)c*4u;
    e->raw[ENT_DELTA1]=motion[p]; e->raw[ENT_DELTA1+1]=motion[p+1];
    e->raw[ENT_DELTA0]=motion[p+2]; e->raw[ENT_DELTA0+1]=motion[p+3];
}

static int entity27_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) return enemy_init_standard(e,27,gaw_enemy_configs[27]);
    if ((entity_map_descriptor(e,0,-4)&0x8000u)!=0) { gaw_entity_clear(e); return 1; }
    entity_cull_common(e); return 1;
}

static int entity28_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) {
        e->raw[0x08]=entity28_config[0]; e->raw[0x09]=entity28_config[1]; e->raw[ENT_ATTACK]=entity28_config[2];
        e->raw[0x11]=(uint8_t)(e->raw[0x11]+entity28_config[3]); e->raw[ENT_ANIM_FRAMES]=entity28_config[4]; e->raw[ENT_ANIM_DELAY]=entity28_config[5];
        e->raw[0x20]=8; e->raw[ENT_STATE]=2; e->raw[ENT_FLAGS]=3;
    }
    if (e->raw[ENT_STATE]==2) {
        toward_player_motion_only(e,entity28_config+6); e->raw[ENT_STATE]=4; e->raw[ENT_MOTION_PHASE]=0x10; return 1;
    }
    if (e->raw[ENT_STATE]==4 && e->raw[ENT_MOTION_PHASE]==0) {
        if (e->raw[0x11]<8 || e->raw[0x11]>=0xA0 || e->raw[0x13]<8 || e->raw[0x13]>=0xF8) { gaw_entity_clear(e); return 1; }
        e->raw[0x20]=(uint8_t)(e->raw[0x20]-1u); if (e->raw[0x20]==0) gaw_entity_clear(e); else e->raw[ENT_STATE]=2;
    }
    return 1;
}

static void ballistic_update(GawEntity *e) {
    uint16_t v;
    v=(uint16_t)(gaw_entity_get16(e,0x22)+gaw_entity_get16(e,0x20)); set_word_bytes(e,0x22,v);
    v=(uint16_t)(gaw_entity_get16(e,0x26)+gaw_entity_get16(e,0x24)); set_word_bytes(e,0x26,v);
    v=(uint16_t)(gaw_entity_get16(e,0x28)+gaw_entity_get16(e,0x2E)); set_word_bytes(e,0x28,v);
    int32_t off=(int16_t)gaw_entity_get16(e,0x2A)+(int16_t)gaw_entity_get16(e,0x28);
    if (off<0) off=0;
    set_word_bytes(e,0x2A,(uint16_t)off);
    set_word_bytes(e,ENT_ACCUM0,(uint16_t)(gaw_entity_get16(e,0x26)-(uint16_t)off));
    set_word_bytes(e,ENT_ACCUM1,gaw_entity_get16(e,0x22));
}

static int entity29_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) {
        e->raw[0x08]=0x4E; e->raw[0x09]=0x90; e->raw[ENT_ANIM_DELAY]=4; e->raw[ENT_ANIM_FRAMES]=2; e->raw[ENT_ATTACK]=0x10;
        set_word_bytes(e,0x2E,0xFFF0); e->raw[0x23]=e->raw[0x13]; e->raw[0x27]=e->raw[0x11]; e->raw[ENT_STATE]=2;
        /* $41B9 falls directly into $41BD. */
    }
    if (e->raw[ENT_STATE]==2) {
        e->raw[ENT_FLAGS]|=3u; unsigned d=e->raw[ENT_DIRECTION]; if (d>1) d&=1u;
        const uint8_t *p=entity29_launch+d*5u; e->raw[0x20]=p[0]; e->raw[0x21]=p[1]; e->raw[0x24]=p[2]; e->raw[0x25]=p[3]; e->raw[ENT_DIRECTION]=p[4];
        set_word_bytes(e,0x28,0x0200); e->raw[ENT_STATE]=4; ballistic_update(e); return 1;
    }
    if (e->raw[ENT_STATE]==4) {
        if (gaw_entity_get16(e,0x2A)==0) gaw_entity_clear(e); else ballistic_update(e);
    }
    return 1;
}

static int entity31_handler(GawEntity *e) {
    if (e->raw[ENT_STATE]==0) {
        set_word_bytes(e,0x2E,0xFFD8); e->raw[ENT_FLAGS]|=3u; e->raw[0x23]=e->raw[0x13]; e->raw[0x27]=e->raw[0x11]; e->raw[ENT_STATE]=2;
    }
    if (e->raw[ENT_STATE]==2) {
        e->raw[0x08]=entity31_config[0]; e->raw[0x09]=entity31_config[1]; e->raw[ENT_ATTACK]=entity31_config[2];
        e->raw[0x11]=(uint8_t)(e->raw[0x11]+entity31_config[3]); e->raw[ENT_ANIM_FRAMES]=entity31_config[4]; e->raw[ENT_ANIM_DELAY]=entity31_config[5];
        toward_player_motion_only(e,entity31_config+6);
        set_word_bytes(e,0x20,gaw_entity_get16(e,ENT_DELTA1)); set_word_bytes(e,0x24,gaw_entity_get16(e,ENT_DELTA0));
        set_word_bytes(e,0x28,0x0210); e->raw[ENT_MOTION_PHASE]=0x60; e->raw[ENT_STATE]=6; ballistic_update(e); return 1;
    }
    if (e->raw[ENT_STATE]==4) { set_word_bytes(e,0x28,0x0210); e->raw[ENT_MOTION_PHASE]=0x60; e->raw[ENT_STATE]=6; ballistic_update(e); return 1; }
    if (e->raw[ENT_STATE]==6) {
        if (e->raw[0x11]<8 || e->raw[0x11]>=0xA0 || e->raw[0x13]<8 || e->raw[0x13]>=0xF8 || e->raw[ENT_MOTION_PHASE]==0) { gaw_entity_clear(e); return 1; }
        if (gaw_entity_get16(e,0x2A)!=0) ballistic_update(e); else e->raw[ENT_STATE]=4;
    }
    return 1;
}


/* $48F3/$48F6 for ordinary entities (type != $34). Returns 1 when the
   requested direction is blocked by screen bounds or a descriptor whose
   high byte has one of the original $A0 mask bits. */
static int entity_direction_blocked(const GawEntity *e, uint8_t direction) {
    uint16_t d;
    switch (direction & 3u) {
        case 0: /* left: $4929, samples two vertically adjacent descriptors */
            if (e->raw[0x11] < 0x19u) return 1;
            d=entity_map_descriptor(e,-8,-16);
            return ((((uint8_t)(d>>8)) | ((uint8_t)(entity_map_descriptor(e,0,-16)>>8))) & 0xA0u) != 0;
        case 1: /* right: $4934, two vertically adjacent descriptors */
            if (e->raw[0x11] >= 0x98u) return 1;
            d=entity_map_descriptor(e,-8,0);
            return ((((uint8_t)(d>>8)) | ((uint8_t)(entity_map_descriptor(e,0,0)>>8))) & 0xA0u) != 0;
        case 2: /* up: $4905 */
            if (e->raw[0x13] < 0x11u) return 1;
            d=entity_map_descriptor(e,-16,-8);
            return (((uint8_t)(d>>8)) & 0xA0u) != 0;
        default: /* down: $4910 */
            if (e->raw[0x13] >= 0xE8u) return 1;
            d=entity_map_descriptor(e,8,-8);
            return (((uint8_t)(d>>8)) & 0xA0u) != 0;
    }
}

/* $4859: choose one of four directions from Z80-R entropy and accept it only
   when the edge/map test succeeds. */
static int entity_choose_random_direction(GawEntity *e) {
    uint8_t d=(uint8_t)(gaw_platform_entropy8() & 3u);
    if (entity_direction_blocked(e,d)) return 0;
    e->raw[ENT_DIRECTION]=d;
    return 1;
}

/* $4893: only succeeds when Arthur and the entity share the same 16-pixel
   row or column; on success it points the entity toward Arthur. */
static int entity_direction_toward_player_aligned(GawEntity *e) {
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR), px=gaw_ram_read8(PLAYER_X_ADDR);
    if ((py&0xF0u)==(e->raw[0x13]&0xF0u)) {
        e->raw[ENT_DIRECTION]=(px>=e->raw[0x11])?1u:0u;
        return 1;
    }
    if ((px&0xF0u)==(e->raw[0x11]&0xF0u)) {
        e->raw[ENT_DIRECTION]=(py>=e->raw[0x13])?3u:2u;
        return 1;
    }
    return 0;
}

/* $48D0 with HL=$85D9. */
static void entity32_load_motion(GawEntity *e) {
    e->raw[ENT_MOTION_PHASE]=entity32_motion[0];
    unsigned p=1u+(unsigned)(e->raw[ENT_DIRECTION]&3u)*4u;
    e->raw[ENT_DELTA0]=entity32_motion[p];
    e->raw[ENT_DELTA0+1]=entity32_motion[p+1];
    e->raw[ENT_DELTA1]=entity32_motion[p+2];
    e->raw[ENT_DELTA1+1]=entity32_motion[p+3];
}

/* $57F8 with BC=$0004. The original samples a packed $DC00 cell from R,
   accepts tile IDs {00,03,01,3A}, keeps at least 16 px from Arthur on both
   axes, then chooses an initial direction from R. */
static int entity32_try_spawn(GawEntity *e) {
    if ((gaw_ram_read8(RAM_FRAME_COUNTER)&7u)!=(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX)&7u)) return 0;
    uint8_t packed=(uint8_t)((gaw_platform_entropy8()&0x7Fu)+0x10u);
    if ((((uint8_t)(packed-1u))&0x0Fu)>=0x0Eu) return 0;
    uint8_t tile=gaw_ram_read8((uint16_t)(0xDC00u+packed));
    int allowed=0; for (unsigned i=0;i<4;++i) if (tile==entity_spawn_tiles16[i]) { allowed=1; break; }
    if (!allowed) return 0;
    uint8_t y=(uint8_t)((packed&0x0Fu)*16u+8u);
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR);
    unsigned dy=(py>=y)?(unsigned)(py-y):(unsigned)(y-py);
    if (dy<0x10u) return 0;
    uint8_t x=(uint8_t)((packed&0xF0u)+0x10u);
    uint8_t px=gaw_ram_read8(PLAYER_X_ADDR);
    unsigned dx=(px>=x)?(unsigned)(px-x):(unsigned)(x-px);
    if (dx<0x10u) return 0;
    e->raw[0x13]=y; e->raw[0x11]=x;
    e->raw[ENT_DIRECTION]=(uint8_t)(gaw_platform_entropy8()&3u);
    e->raw[ENT_FLAGS]|=3u;
    return 1;
}

/* $495E/$4965: allocate one of slots 24..31 and copy the fields used by the
   auxiliary entity. C01B bit 6 globally suppresses these spawns. */
static int entity_spawn_aux(GawEntity *parent, uint8_t type) {
    if (gaw_ram_read8(0xC01B)&0x40u) return 0;
    for (unsigned i=24;i<32;++i) {
        GawEntity *child=gaw_entity(i);
        if (child->raw[ENT_TYPE]!=0) continue;
        child->raw[ENT_TYPE]=type;
        child->raw[ENT_GFX_ID]=parent->raw[ENT_GFX_ID];
        child->raw[0x13]=parent->raw[0x13];
        child->raw[0x11]=parent->raw[0x11];
        child->raw[ENT_DIRECTION]=parent->raw[ENT_DIRECTION];
        return 1;
    }
    return 0;
}
static GawEntity *entity_spawn_aux_ptr(GawEntity *parent,uint8_t type){
    if(gaw_ram_read8(0xC01B)&0x40u)return NULL;
    for(unsigned i=24;i<32;++i){GawEntity *child=gaw_entity(i);if(child->raw[ENT_TYPE]!=0)continue;child->raw[ENT_TYPE]=type;child->raw[ENT_GFX_ID]=parent->raw[ENT_GFX_ID];child->raw[0x13]=parent->raw[0x13];child->raw[0x11]=parent->raw[0x11];child->raw[ENT_DIRECTION]=parent->raw[ENT_DIRECTION];return child;}
    return NULL;
}

/* Type 32 / $4C5D -> bank-2 table $8522. */
static int entity32_handler(GawEntity *e) {
    switch (e->raw[ENT_STATE]) {
        case 0:
            if (!entity32_try_spawn(e)) return 1;
            e->raw[0x08]=0xFA; e->raw[0x09]=0x84;
            e->raw[ENT_ANIM_DELAY]=0x10; e->raw[ENT_ANIM_FRAMES]=4;
            e->raw[ENT_STATE]=2;
            return 1;
        case 2:
            if (e->raw[ENT_ANIM_FRAME]!=3) return 1;
            e->raw[ENT_ANIM_FRAME]=0;
            e->raw[0x08]=0x2E; e->raw[0x09]=0x85;
            e->raw[ENT_ANIM_DELAY]=0x0A; e->raw[ENT_ANIM_FRAMES]=2;
            e->raw[ENT_STATE]=4;
            return 1;
        case 4:
            if (!entity_choose_random_direction(e)) return 1;
            /* original falls through into state 6 */
            entity32_load_motion(e); e->raw[ENT_STATE]=8; return 1;
        case 6:
            entity32_load_motion(e); e->raw[ENT_STATE]=8; return 1;
        case 8: {
            if (e->raw[ENT_MOTION_PHASE]!=0) return 1;
            if (entity_direction_blocked(e,e->raw[ENT_DIRECTION])) { e->raw[ENT_STATE]=4; return 1; }
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
            if (r<2u) { e->raw[ENT_STATE]=4; return 1; }
            if (r<8u) { e->raw[ENT_STATE]=6; return 1; }
            if (!entity_direction_toward_player_aligned(e)) { e->raw[ENT_STATE]=6; return 1; }
            gaw_entity_set16(e,ENT_DELTA1,0); gaw_entity_set16(e,ENT_DELTA0,0);
            e->raw[ENT_MOTION_PHASE]=0x10; e->raw[ENT_STATE]=0x0A; return 1;
        }
        case 0x0A:
            if (e->raw[ENT_MOTION_PHASE]!=0) return 1;
            /* $85D6 maps type $20/$21/$22 to spawned types $10/$11/$12. */
            if (e->raw[ENT_TYPE]>=0x20u && e->raw[ENT_TYPE]<=0x22u)
                (void)entity_spawn_aux(e,entity32_spawn_types[e->raw[ENT_TYPE]-0x20u]);
            e->raw[ENT_MOTION_PHASE]=8; e->raw[ENT_STATE]=0x0C; return 1;
        case 0x0C:
            if (e->raw[ENT_MOTION_PHASE]==0) e->raw[ENT_STATE]=4;
            return 1;
        default:
            return 1;
    }
}


/* Types $3D/$3E (61/62, table $941A) and $40 (64, table $963B).
   These are the same wander/aim/fire machine with different graphics,
   random thresholds and projectile type. */
static int entity61_62_64_handler(GawEntity *e,uint8_t type){
    const int is64=(type==64u);uint8_t st=e->raw[ENT_STATE];
    switch(st){
        case 0:
            if(!entity32_try_spawn(e))return 1;
            e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;return 1;
        case 2:
            if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;
            e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=is64?0xB2:0xAA;e->raw[0x09]=0x8D-(is64?0:1); /* B2:8D / AA:8C */
            e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;
            /* $9426/$9647 falls straight into the state-4 chooser. */
            if(!entity_choose_random_direction(e))return 1;
            entity32_load_motion(e);e->raw[ENT_STATE]=8;return 1;
        case 4:
            if(!entity_choose_random_direction(e))return 1;
            /* fall through to state 6 */
            entity32_load_motion(e);e->raw[ENT_STATE]=8;return 1;
        case 6:
            entity32_load_motion(e);e->raw[ENT_STATE]=8;return 1;
        case 8:{
            if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu),first=is64?2u:4u;
            if(r<first){e->raw[ENT_STATE]=4;return 1;}
            if(r<(uint8_t)(first+6u)){e->raw[ENT_STATE]=6;return 1;}
            if(!entity_direction_toward_player_aligned(e)){e->raw[ENT_STATE]=6;return 1;}
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
            entity32_load_motion(e);e->raw[ENT_STATE]=0x0A;return 1;
        }
        case 0x0A:
            if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
            if((gaw_platform_entropy8()&0x0Fu)<4u){e->raw[ENT_STATE]=4;return 1;}
            (void)entity_spawn_aux(e,is64?0x1Bu:0x1Au);e->raw[ENT_STATE]=6;return 1;
        default:return 1;
    }
}

static int16_t sine_scaled(uint8_t phase, uint8_t amplitude, int quarter_turn) {
    uint8_t p=(uint8_t)(phase+(quarter_turn?0x40u:0u));
    int16_t base=(int16_t)((int8_t)sine_table[p])*2;
    return (int16_t)(base*(int16_t)amplitude);
}
static void load_motion_record(GawEntity *e,const uint8_t rec[17]) {
    e->raw[ENT_MOTION_PHASE]=rec[0]; unsigned p=1u+(e->raw[ENT_DIRECTION]&3u)*4u;
    e->raw[ENT_DELTA0]=rec[p];e->raw[ENT_DELTA0+1]=rec[p+1];e->raw[ENT_DELTA1]=rec[p+2];e->raw[ENT_DELTA1+1]=rec[p+3];
}

/* Types $23-$25 (35..37), bank-2 table $85FB. */
static int entity35_37_handler(GawEntity *e) {
    uint8_t type=e->raw[ENT_TYPE];
    if (e->raw[ENT_STATE]==0) {
        if (!entity32_try_spawn(e)) return 1;
        e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;return 1;
    }
    if (e->raw[ENT_STATE]==2) {
        if (e->raw[ENT_ANIM_FRAME]!=3) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x26]=e->raw[0x13];e->raw[0x28]=e->raw[0x11];
        e->raw[0x08]=0xEE;e->raw[0x09]=0x85;e->raw[ENT_ANIM_DELAY]=5;e->raw[ENT_ANIM_FRAMES]=2;
        uint8_t q=gaw_ram_read8(RAM_ENTITY_SLOT_INDEX); q=(uint8_t)((q>>3)|(q<<5)); e->raw[0x29]=q;
        gaw_entity_set16(e,0x21,0);gaw_entity_set16(e,0x23,0);e->raw[ENT_STATE]=4;return 1;
    }
    if (e->raw[ENT_STATE]!=4) return 1;
    unsigned k=(unsigned)(type-35u)*2u; int16_t mag=(int16_t)u16le_at(entity35_target_offsets+k);
    int16_t target=((int)gaw_ram_read8(PLAYER_Y_ADDR)-(int)e->raw[0x13]>=0)?mag:(int16_t)-mag;
    int16_t vy=(int16_t)gaw_entity_get16(e,0x21), py=(int16_t)gaw_entity_get16(e,0x25);
    if ((vy<0?-vy:vy)<0x0200) vy=(int16_t)(vy+target);
    if ((uint8_t)(((uint16_t)py>>8)-0x20u)>=0xC0u) vy=(int16_t)(vy/2);
    gaw_entity_set16(e,0x21,(uint16_t)vy); py=(int16_t)(py+vy); gaw_entity_set16(e,0x25,(uint16_t)py);
    target=((int)gaw_ram_read8(PLAYER_X_ADDR)-(int)e->raw[0x11]>=0)?mag:(int16_t)-mag;
    int16_t vx=(int16_t)gaw_entity_get16(e,0x23), px=(int16_t)gaw_entity_get16(e,0x27);
    if ((vx<0?-vx:vx)<0x0200) vx=(int16_t)(vx+target);
    if ((uint8_t)(((uint16_t)px>>8)-0x20u)>=0x58u) vx=(int16_t)(vx/2);
    gaw_entity_set16(e,0x23,(uint16_t)vx); px=(int16_t)(px+vx); gaw_entity_set16(e,0x27,(uint16_t)px);
    if (e->raw[0x2A]!=0x10) ++e->raw[0x2A];
    int16_t wob=sine_scaled(e->raw[0x29],e->raw[0x2A],1); e->raw[0x13]=(uint8_t)((uint16_t)(py+wob)>>8);
    if (e->raw[0x2B]!=0x0C) ++e->raw[0x2B];
    wob=sine_scaled(e->raw[0x29],e->raw[0x2B],0); e->raw[0x11]=(uint8_t)((uint16_t)(px+wob)>>8);
    e->raw[0x29]=(uint8_t)(e->raw[0x29]+5u);
    static const uint8_t face[4]={1,2,0,3}; e->raw[ENT_DIRECTION]=face[(e->raw[0x29]>>6)&3u];
    if (type==36 && e->raw[ENT_MOTION_PHASE]==0) { (void)entity_spawn_aux(e,0x13);e->raw[ENT_MOTION_PHASE]=0x80; }
    if (type==37 && e->raw[ENT_MOTION_PHASE]==0) { (void)entity_spawn_aux(e,0x15);e->raw[ENT_MOTION_PHASE]=0x80; }
    return 1;
}

/* Types $26-$28 (38..40), wrapper $4C78 + table $8756. */
static int entity38_40_handler(GawEntity *e) {
    uint8_t type=e->raw[ENT_TYPE];
    switch(e->raw[ENT_STATE]) {
        case 0:
            if(!entity32_try_spawn(e)) break;
            e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;break;
        case 2:
            if(e->raw[ENT_ANIM_FRAME]!=3) break;
            e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x24;e->raw[0x09]=0x86;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=entity38_variant[type-38u];e->raw[ENT_STATE]=4;break;
        case 4:
            if(entity_choose_random_direction(e)) e->raw[ENT_STATE]=6;
            break;
        case 6:
            load_motion_record(e,(type==40)?entity32_motion:entity38_motion_fast);e->raw[ENT_ANIM_DELAY]=e->raw[ENT_MOTION_PHASE];e->raw[ENT_STATE]=8;break;
        case 8:
            if(e->raw[ENT_MOTION_PHASE]!=0) break;
            if(e->raw[0x20] && --e->raw[0x20]==0) { e->raw[ENT_STATE]=4;break; }
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION]) || (gaw_platform_entropy8()&0x0Fu)==0) e->raw[ENT_STATE]=4; else e->raw[ENT_STATE]=6;
            break;
        default: break;
    }
    uint8_t dmg=e->raw[ENT_PENDING_DAMAGE];
    if(dmg && e->raw[ENT_HP]>dmg && e->raw[0x20]==2u) {
        --e->raw[0x20]; unsigned slot=24u+(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX)&7u); GawEntity *c=gaw_entity(slot);
        if(c && c->raw[ENT_TYPE]==0) { memcpy(c->raw,e->raw,0x21u); e->raw[ENT_PENDING_DAMAGE]=dmg; }
    }
    return 1;
}

/* Types $29-$2A (41..42), table $87DE. */
static int entity41_42_handler(GawEntity *e) {
    uint8_t type=e->raw[ENT_TYPE];
    switch(e->raw[ENT_STATE]) {
        case 0:
            if(!entity32_try_spawn(e)) break;
            e->raw[0x08]=0xFA; e->raw[0x09]=0x84; e->raw[ENT_ANIM_DELAY]=0x10; e->raw[ENT_ANIM_FRAMES]=4; e->raw[ENT_STATE]=2;
            break;
        case 2:
            if(e->raw[ENT_ANIM_FRAME]==3){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}
            break;
        case 4:
            e->raw[0x08]=0x48;e->raw[0x09]=0x86;
            if(entity_choose_random_direction(e))e->raw[ENT_STATE]=6;
            break;
        case 6:
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION]) && !entity_choose_random_direction(e)) break;
            load_motion_record(e,type==41?entity32_motion:entity42_motion);e->raw[ENT_STATE]=8;
            break;
        case 8: {
            if(e->raw[ENT_MOTION_PHASE]!=0) break;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;break;}
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
            if(r<2u){e->raw[ENT_STATE]=4;break;}
            if(r<8u || type==41 || !entity_direction_toward_player_aligned(e)){e->raw[ENT_STATE]=6;break;}
            gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=0x0A;
            break;
        }
        case 0x0A:
            if(e->raw[ENT_MOTION_PHASE]==0){(void)entity_spawn_aux(e,0x17);e->raw[0x08]=0xD8;e->raw[0x09]=0x86;e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=0x0C;}
            break;
        case 0x0C:
            if(e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=4;
            break;
        default:break;
    }
    return 1;
}

static uint8_t entity_world_cell_at(const GawEntity *e,int8_t dy,int8_t dx) {
    uint8_t x=(uint8_t)(e->raw[0x11]+(uint8_t)dx), y=(uint8_t)(e->raw[0x13]+(uint8_t)dy);
    return (uint8_t)((x&0xF0u)|((y&0xF0u)>>4));
}
/* Type 43, table $8893. */
static int entity43_handler(GawEntity *e) {
    switch(e->raw[ENT_STATE]) {
        case 0:
            if(entity32_try_spawn(e)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}break;
        case 2:
            if(e->raw[ENT_ANIM_FRAME]==3){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}break;
        case 4:
            e->raw[0x08]=0x2C;e->raw[0x09]=0x87;if(entity_choose_random_direction(e))e->raw[ENT_STATE]=6;
            break;
        case 6:
            load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;break;
        case 8: {
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;break;}
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
            if(r<4u){e->raw[ENT_STATE]=4;break;}
            if(r<14u){e->raw[ENT_STATE]=6;break;}
            uint8_t cell=entity_world_cell_at(e,-8,-16);
            if(gaw_ram_read8((uint16_t)(0xDC00u+cell))!=3u || (e->raw[0x13]&8u)==0 || (e->raw[0x11]&8u)!=0){e->raw[ENT_STATE]=6;break;}
            gaw_world_set_tile(cell,0x66);e->raw[0x08]=0x56;e->raw[0x09]=0x87;gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=0x0A;break;
        }
        case 0x0A:
            if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=0x0C;}break;
        case 0x0C:
            if(e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=4;
            break;
        default:break;
    }
    return 1;
}
/* Type 44, table $8942. */
static int entity44_handler(GawEntity *e) {
    switch(e->raw[ENT_STATE]) {
        case 0:
            if(entity32_try_spawn(e)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}break;
        case 2:
            if(e->raw[ENT_ANIM_FRAME]==3){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x80;e->raw[0x09]=0x87;e->raw[ENT_ANIM_DELAY]=5;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}break;
        case 4:
            if(entity_choose_random_direction(e))e->raw[ENT_STATE]=6;
            break;
        case 6:
            load_motion_record(e,entity42_motion);e->raw[ENT_STATE]=8;break;
        case 8: {
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;break;}
            if(e->raw[ENT_DIRECTION]&2u){e->raw[ENT_STATE]=6;break;}
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
            if(r<4u){e->raw[ENT_STATE]=4;break;}
            if(r<14u){e->raw[ENT_STATE]=6;break;}
            e->raw[0x08]=0xAA;e->raw[0x09]=0x87;gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_STATE]=0x0A;break;
        }
        case 0x0A:
            if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0x80;e->raw[0x09]=0x87;e->raw[ENT_STATE]=4;}break;
        default:break;
    }
    return 1;
}

static int entity_try_spawn_list(GawEntity *e,uint8_t list_off,uint8_t count) {
    if ((gaw_ram_read8(RAM_FRAME_COUNTER)&7u)!=(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX)&7u)) return 0;
    uint8_t packed=(uint8_t)((gaw_platform_entropy8()&0x7Fu)+0x10u);
    if ((((uint8_t)(packed-1u))&0x0Fu)>=0x0Eu) return 0;
    uint8_t tile=gaw_ram_read8((uint16_t)(0xDC00u+packed)); int ok=0;
    for(unsigned i=0;i<count && (unsigned)list_off+i<16u;++i)if(tile==entity_spawn_tiles16[list_off+i]){ok=1;break;}
    if(!ok)return 0;
    uint8_t y=(uint8_t)((packed&0x0Fu)*16u+8u),x=(uint8_t)((packed&0xF0u)+0x10u);
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);
    unsigned dy=py>=y?py-y:y-py,dx=px>=x?px-x:x-px;if(dy<16u||dx<16u)return 0;
    e->raw[0x13]=y;e->raw[0x11]=x;e->raw[ENT_DIRECTION]=(uint8_t)(gaw_platform_entropy8()&3u);e->raw[ENT_FLAGS]|=3u;return 1;
}
static uint8_t fixed_data8(uint16_t a){return (a>=0x58BCu && a<0x5B30u)?entity_fixed_position_data[a-0x58BCu]:0;}
static uint16_t fixed_data16(uint16_t a){return (uint16_t)(fixed_data8(a)|((uint16_t)fixed_data8((uint16_t)(a+1u))<<8));}
/* $5878: fixed position selected by world cell and local slot 16..23. */
static void entity_place_fixed(GawEntity *e) {
    uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID); uint16_t list,ptrtab; unsigned count;
    if(gaw_ram_read8(0xC0BA)==0){list=0x58BC;ptrtab=0x58C7;count=11;}else{list=0x5919;ptrtab=0x5952;count=57;}
    unsigned rem=0;for(unsigned j=0;j<count;++j)if(fixed_data8((uint16_t)(list+j))==cell){rem=count-j-1u;break;}
    uint16_t posbase=fixed_data16((uint16_t)(ptrtab+2u*rem));unsigned slot=(unsigned)(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX)-0x10u)&7u;
    uint16_t pos=fixed_data16((uint16_t)(posbase+2u*slot));e->raw[0x13]=(uint8_t)pos;e->raw[0x11]=(uint8_t)(pos>>8);e->raw[ENT_FLAGS]|=3u;
}
/* Type 45 / $89D4. */
static int entity45_handler(GawEntity *e){
    if(e->raw[ENT_STATE]==0){entity_place_fixed(e);e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_STATE]=2;return 1;}
    if(e->raw[ENT_STATE]==2 && e->raw[ENT_MOTION_PHASE]==0){if((gaw_platform_entropy8()&0x0Fu)>=8u)(void)entity_spawn_aux(e,0x14);e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x71u);}return 1;
}
/* Types 46..47 / $8A0F. */
static int entity46_47_handler(GawEntity *e){
    uint8_t type=e->raw[ENT_TYPE];
    switch(e->raw[ENT_STATE]){
        case 0:
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            if(!entity_try_spawn_list(e,type==47?1u:4u,type==47?5u:2u))break;
            e->raw[0x08]=0xD4;e->raw[0x09]=0x87;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=2;break;
        case 2:
            if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0xDC;e->raw[0x09]=0x87;e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=5;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_STATE]=4;}break;
        case 4:
            if(e->raw[ENT_ANIM_FRAME]==4){(void)entity_spawn_aux(e,type==46?0x14:0x15);e->raw[0x08]=0xE4;e->raw[0x09]=0x87;e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=5;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_STATE]=6;}break;
        case 6:
            if(e->raw[ENT_ANIM_FRAME]==4){e->raw[0x08]=0xD4;e->raw[0x09]=0x87;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=8;}break;
        case 8:
            if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x1Fu)|0x60u);e->raw[ENT_STATE]=0;}break;
        default:break;
    }return 1;
}


/* Type 48 / $8ACD: a visual/linked child that follows fields +$23/+$27
   of the preceding 0x30-byte slot (IX-13 / IX-9). */
static int entity48_handler(GawEntity *e) {
    uint16_t a=gaw_entity_addr(e);
    if(e->raw[ENT_STATE]==0){e->raw[ENT_FLAGS]=1;e->raw[0x08]=0x5E;e->raw[0x09]=0x88;}
    e->raw[0x13]=gaw_ram_read8((uint16_t)(a-13u));
    e->raw[0x11]=gaw_ram_read8((uint16_t)(a-9u));
    return 1;
}

static uint8_t erel8(const GawEntity *e,unsigned off){return gaw_ram_read8((uint16_t)(gaw_entity_addr(e)+off));}
static void ewrel8(GawEntity *e,unsigned off,uint8_t v){gaw_ram_write8((uint16_t)(gaw_entity_addr(e)+off),v);}
static uint16_t erel16(const GawEntity *e,unsigned off){return (uint16_t)(erel8(e,off)|((uint16_t)erel8(e,off+1u)<<8));}
static void ewrel16(GawEntity *e,unsigned off,uint16_t v){ewrel8(e,off,(uint8_t)v);ewrel8(e,off+1u,(uint8_t)(v>>8));}
static void entity49_50_physics(GawEntity *e){
    uint16_t y=(uint16_t)(erel16(e,0x22)+erel16(e,0x20));ewrel16(e,0x22,y);
    uint16_t x=(uint16_t)(erel16(e,0x26)+erel16(e,0x24));ewrel16(e,0x26,x);
    int16_t gravity=(e->raw[ENT_TYPE]==50)?-0x80:-0x20;
    int16_t vv=(int16_t)erel16(e,0x28);vv=(int16_t)(vv+gravity);ewrel16(e,0x28,(uint16_t)vv);
    int16_t z=(int16_t)erel16(e,0x2A);z=(int16_t)(z+vv);if(z<0)z=0;ewrel16(e,0x2A,(uint16_t)z);
    ewrel16(e,ENT_ACCUM0,(uint16_t)(x-(uint16_t)z));ewrel16(e,ENT_ACCUM1,y);
    uint16_t spr=0x8871u;if(e->raw[ENT_STATE]>=0x0Au && erel8(e,0x2B)<3u)spr=0x888Au;e->raw[0x08]=(uint8_t)spr;e->raw[0x09]=(uint8_t)(spr>>8);
}
static int entity49_50_handler(GawEntity *e){
    uint8_t type=e->raw[ENT_TYPE];
    if(e->raw[ENT_STATE]==0){if(entity32_try_spawn(e)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(e->raw[ENT_STATE]==2){
        if(e->raw[ENT_ANIM_FRAME]!=3)return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_FRAMES]=0;ewrel8(e,0x2A,0);ewrel8(e,0x2B,0);e->raw[ENT_FLAGS]|=3u;
        ewrel8(e,0x23,e->raw[0x13]);ewrel8(e,0x27,e->raw[0x11]);ewrel8(e,0x30,0x30);ewrel8(e,0x32,e->raw[ENT_GFX_ID]);
        ewrel16(e,0x20,0);ewrel16(e,0x24,0);ewrel16(e,0x28,type==50?0x0200u:0x0100u);e->raw[ENT_STATE]=6;entity49_50_physics(e);return 1;
    }
    if(e->raw[ENT_STATE]==4){ewrel16(e,0x20,0);ewrel16(e,0x24,0);ewrel16(e,0x28,type==50?0x0200u:0x0100u);e->raw[ENT_STATE]=6;entity49_50_physics(e);return 1;}
    if(e->raw[ENT_STATE]==6){if(erel16(e,0x2A)!=0){entity49_50_physics(e);return 1;}e->raw[ENT_STATE]=(gaw_platform_entropy8()&3u)?4u:8u;entity49_50_physics(e);return 1;}
    if(e->raw[ENT_STATE]==8){
        const uint8_t *tab=type==50?entity50_records:entity49_records;unsigned ri=(unsigned)(gaw_platform_entropy8()&7u)*8u;const uint8_t *q=tab+ri;uint8_t flags=q[4];
        uint8_t bx=erel8(e,0x27),by=erel8(e,0x23);int bad=(bx<0x31u&&(flags&1u))||(bx>=0x80u&&(flags&2u))||(by<0x29u&&(flags&4u))||(by>=0xD8u&&(flags&8u));
        if(!bad){uint16_t d=entity_map_descriptor(e,(int8_t)q[6],(int8_t)q[5]);uint16_t d2=entity_map_descriptor(e,(int8_t)(q[6]+8u),(int8_t)q[5]);if((((uint8_t)(d>>8)|(uint8_t)(d2>>8))&0xE0u)!=0)bad=1;}
        if(bad){e->raw[ENT_STATE]=4;ewrel16(e,0x20,0);ewrel16(e,0x24,0);ewrel16(e,0x28,type==50?0x0200u:0x0100u);entity49_50_physics(e);return 1;}
        ewrel16(e,0x20,(uint16_t)(q[0]|((uint16_t)q[1]<<8)));ewrel16(e,0x24,(uint16_t)(q[2]|((uint16_t)q[3]<<8)));e->raw[ENT_DIRECTION]=q[7];ewrel16(e,0x28,type==50?0x0420u:0x0210u);e->raw[ENT_STATE]=0x0A;entity49_50_physics(e);return 1;
    }
    if(e->raw[ENT_STATE]==0x0A){if(erel16(e,0x2A)==0)e->raw[ENT_STATE]=8;entity49_50_physics(e);return 1;}
    return 1;
}

/* Types 51/52, wrappers $4CDE/$4CE4 -> bank-2 tables $8D23/$8D37. */
static void entity51_choose_ballistic(GawEntity *e){
    uint8_t q=(uint8_t)(gaw_platform_entropy8()&3u);
    if(q<2u && e->raw[0x13]<0x48u) q|=2u;
    else if(q>=2u && e->raw[0x13]>=0xC8u) q&=(uint8_t)~2u;
    e->raw[0x2C]=q; const uint8_t *p=entity51_probe+(unsigned)q*3u;
    e->raw[ENT_DIRECTION]=p[0];
    uint16_t d=entity_map_descriptor(e,(int8_t)p[1],(int8_t)p[2]);
    if((((uint8_t)(d>>8))&0xC0u)!=0xC0u){e->raw[ENT_STATE]=2;return;}
    e->raw[ENT_FLAGS]|=1u;e->raw[0x08]=0x9D;e->raw[0x09]=0x88;e->raw[ENT_ANIM_DELAY]=0x0D;e->raw[ENT_ANIM_FRAMES]=3;
    gaw_entity_set16(e,0x2E,0xFFC0u);e->raw[ENT_STATE]=0x0C;
}
static int entity51_52_handler(GawEntity *e){
    uint8_t type=e->raw[ENT_TYPE], st=e->raw[ENT_STATE];
    if(type==51u && st<=8u){e->raw[ENT_STATE]=0x0A;return 1;}
    switch(st){
        case 0:
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            if(!entity_try_spawn_list(e,5,1))break;
            e->raw[0x08]=0x9D;e->raw[0x09]=0x88;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;
            gaw_entity_set16(e,0x2E,0xFFC0u);e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=2;break;
        case 2:
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x63;e->raw[0x09]=0x89;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;break;
        case 4:
            if(entity_choose_random_direction(e)) e->raw[ENT_STATE]=6;
            break;
        case 6:
            load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;break;
        case 8: {
            if(e->raw[ENT_MOTION_PHASE]!=0)break;
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;break;}
            uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
            if(r<2u){e->raw[ENT_STATE]=4;break;}
            if(r<8u || r>=9u){e->raw[ENT_STATE]=6;break;}
            if((e->raw[0x11]&0x0Fu)!=0 || (e->raw[0x13]&8u)==0){e->raw[ENT_STATE]=6;break;}
            gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_MOTION_PHASE]=0x10;
            e->raw[0x23]=e->raw[0x13];e->raw[0x27]=e->raw[0x11];e->raw[ENT_STATE]=0x0A;break;
        }
        case 0x0A:
            if(type==51u){
                if(e->raw[ENT_MOTION_PHASE]!=0) break;
                e->raw[ENT_ANIM_FRAME]=0;
                if(!entity_try_spawn_list(e,5,1)) break;
                e->raw[ENT_FLAGS]&=(uint8_t)~1u;
            }
            entity51_choose_ballistic(e);break;
        case 0x0C:
            if(e->raw[ENT_ANIM_FRAME]==2u){e->raw[0x23]=e->raw[0x13];e->raw[0x27]=e->raw[0x11];e->raw[0x08]=0x17;e->raw[0x09]=0x89;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x18;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=0x0E;}break;
        case 0x0E: {
            unsigned q=(unsigned)(e->raw[0x2C]&3u);const uint8_t *p=entity51_ballistic+q*4u;
            gaw_entity_set16(e,0x20,u16le_at(p));gaw_entity_set16(e,0x24,u16le_at(p+2));gaw_entity_set16(e,0x28,0x0420u);e->raw[ENT_STATE]=0x10;ballistic_update(e);break;
        }
        case 0x10:
            if(e->raw[0x2B]==0x20u)(void)entity_spawn_aux(e,0x13);
            if(gaw_entity_get16(e,0x2A)!=0)ballistic_update(e);
            else{e->raw[0x08]=0xE1;e->raw[0x09]=0x88;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x0D;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=0x12;}break;
        case 0x12:
            if(e->raw[ENT_ANIM_FRAME]==3u){
                if(type==51u){e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)|0x79u);e->raw[ENT_STATE]=0x0A;}
                else{e->raw[ENT_DIRECTION]=(uint8_t)(gaw_platform_entropy8()&3u);e->raw[ENT_STATE]=2;}
            }break;
        default:break;
    }
    return 1;
}

static void entity_set_tile_offset(GawEntity *e,int8_t yoff,int8_t xoff,uint8_t tile){
    uint8_t cell=world_cell_from_entity_offset(e,yoff,xoff);gaw_world_set_tile(cell,tile);
}
/* Types 53..55, wrappers $4CEA/$4CF0/$4CF6. */
static void entity53_55_wander_choice(GawEntity *e,uint8_t type){
    if(type==53u){if((gaw_platform_entropy8()&0x0Fu)==0)(void)entity_spawn_aux(e,0x16);}
    else if(type==54u){
        if((gaw_platform_entropy8()&0x0Fu)==0){for(uint8_t b=4;b!=0;--b){GawEntity*c=entity_spawn_aux_ptr(e,0x19);if(!c)break;c->raw[ENT_DIRECTION]=(uint8_t)(b-1u);}}
    }else{if((gaw_platform_entropy8()&7u)==0)(void)entity_spawn_aux(e,0x1E);}
    if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=6;return;}
    uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
    if(r<2u){e->raw[ENT_STATE]=6;return;}
    if(r<8u){e->raw[ENT_STATE]=8;return;}
    e->raw[ENT_STATE]=entity_direction_toward_player_aligned(e)?8u:6u;
}
static int entity53_55_handler(GawEntity *e){
    uint8_t type=e->raw[ENT_TYPE], st=e->raw[ENT_STATE];
    if(st==0){
        if(type==53u){entity_place_fixed(e);e->raw[0x08]=0x8D;e->raw[0x09]=0x89;e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[ENT_STATE]=2;return 1;}
        if(entity32_try_spawn(e)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;
    }
    if(st==2){
        if(type==53u){
            uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;
            if(dy>=0x18u||dx>=0x20u) return 1;
            e->raw[ENT_ANIM_DELAY]=2;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=0x18;e->raw[ENT_FLAGS]|=1u;e->raw[ENT_STATE]=4;
            uint16_t d=entity_map_descriptor(e,-8,-24);entity_set_tile_offset(e,-8,-16,(uint8_t)d==0x6Bu?0x27u:0x01u);d=entity_map_descriptor(e,-8,0);if((uint8_t)d==0x53u)entity_set_tile_offset(e,-8,0,0x01);return 1;
        }
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xB7;e->raw[0x09]=0x89;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=6;st=6;
    }
    if(st==4){
        if(type!=53u){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;}else if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(type==53u) e->raw[ENT_DIRECTION]=1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xB7;e->raw[0x09]=0x89;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=6;st=6;
    }
    if(st==6){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=8;st=8;}
    if(st==8){load_motion_record(e,type==53u?entity53_motion:type==54u?entity38_motion_fast:entity32_motion);e->raw[ENT_STATE]=0x0A;return 1;}
    if(st==0x0A && e->raw[ENT_MOTION_PHASE]==0)entity53_55_wander_choice(e,type);
    return 1;
}

/* Types 56/57, wrapper $4CFC -> bank-2 table $90DB. */
static int entity56_57_handler(GawEntity *e){
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity32_try_spawn(e)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xE1;e->raw[0x09]=0x89;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);if(r<4u){e->raw[ENT_STATE]=4;return 1;}if(r<14u){e->raw[ENT_STATE]=6;return 1;}
        e->raw[ENT_DIRECTION]=(gaw_ram_read8(PLAYER_Y_ADDR)<e->raw[0x13])?2u:3u;gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;(void)entity_spawn_aux(e,0x1F);e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xA1;e->raw[0x09]=0x8A;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=0x0C;return 1;}
    if(st==0x0C){if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0xE1;e->raw[0x09]=0x89;e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=0x0E;}return 1;}
    if(st==0x0E && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=4;
    return 1;
}

/* Types 58/59, wrapper $4D02 -> bank-2 table $919B. */
static int entity58_59_handler(GawEntity *e){
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity_try_spawn_list(e,9,2)){e->raw[0x08]=0xF5;e->raw[0x09]=0x8A;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_FLAGS]&=(uint8_t)~2u;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x1F;e->raw[0x09]=0x8B;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_FLAGS]|=2u;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);if(r<4u){e->raw[ENT_STATE]=4;return 1;}if(r<10u){e->raw[ENT_STATE]=6;return 1;}if(!entity_direction_toward_player_aligned(e)){e->raw[ENT_STATE]=6;return 1;}gaw_entity_set16(e,ENT_DELTA1,0);gaw_entity_set16(e,ENT_DELTA0,0);e->raw[0x08]=0xAF;e->raw[0x09]=0x8B;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x2C]=0x20;e->raw[ENT_STATE]=0x0A;return 1;}
    if(st==0x0A){load_motion_record(e,entity58_charge);e->raw[ENT_STATE]=0x0C;return 1;}
    if(st==0x0C && e->raw[ENT_MOTION_PHASE]==0){if(entity_direction_blocked(e,e->raw[ENT_DIRECTION]) || --e->raw[0x2C]==0){e->raw[0x08]=0x1F;e->raw[0x09]=0x8B;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}else e->raw[ENT_STATE]=0x0A;}
    return 1;
}


/* $4A15: choose the dominant axis toward Arthur, but only commit the new
   direction when the corresponding map edge is traversable. */
static void entity_direction_toward_player_dominant(GawEntity *e) {
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR), px=gaw_ram_read8(PLAYER_X_ADDR);
    unsigned dy=py>=e->raw[0x13]?(unsigned)(py-e->raw[0x13]):(unsigned)(e->raw[0x13]-py);
    unsigned dx=px>=e->raw[0x11]?(unsigned)(px-e->raw[0x11]):(unsigned)(e->raw[0x11]-px);
    if(dx==dy) return;
    uint8_t d;
    if(dx<dy) d=(py>=e->raw[0x13])?3u:2u;
    else d=(px>=e->raw[0x11])?1u:0u;
    if(!entity_direction_blocked(e,d)) e->raw[ENT_DIRECTION]=d;
}

/* Type $3C / 60, bank-2 table $9290.  Wander, pause, then launch itself
   toward Arthur using the eight original $93FA velocity records. */
static void entity60_launch_toward_player(GawEntity *e) {
    static const uint8_t dir_lut[8]={0,3,1,3,0,2,1,2};
    static const uint8_t velocity[32]={
        0xF4,0x00,0xB2,0xFD, 0x4E,0x02,0x0C,0xFF,
        0xF4,0x00,0x4E,0x02, 0x4E,0x02,0xF4,0x00,
        0x0C,0xFF,0xB2,0xFD, 0xB2,0xFD,0x0C,0xFF,
        0x0C,0xFF,0x4E,0x02, 0xB2,0xFD,0xF4,0x00
    };
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR),c=2u;
    unsigned dy=py>=e->raw[0x13]?(unsigned)(py-e->raw[0x13]):(unsigned)(e->raw[0x13]-py);
    if(py<e->raw[0x13]) c|=4u;
    unsigned dx=px>=e->raw[0x11]?(unsigned)(px-e->raw[0x11]):(unsigned)(e->raw[0x11]-px);
    if(px<e->raw[0x11]) c&=(uint8_t)~2u;
    if(dx<dy) ++c;
    e->raw[ENT_DIRECTION]=dir_lut[c&7u];
    unsigned k=(unsigned)(c&7u)*4u;
    e->raw[ENT_DELTA1]=velocity[k];e->raw[ENT_DELTA1+1]=velocity[k+1u];
    e->raw[ENT_DELTA0]=velocity[k+2u];e->raw[ENT_DELTA0+1]=velocity[k+3u];
    e->raw[ENT_STATE]=0x0Eu;e->raw[ENT_MOTION_PHASE]=0x60u;
}
static int entity60_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(entity_try_spawn_list(e,7u,1u)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xEF;e->raw[0x09]=0x8B;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
        if(r<2u){e->raw[ENT_STATE]=4;return 1;} if(r<8u){e->raw[ENT_STATE]=6;return 1;} if(r!=8u){e->raw[ENT_STATE]=6;return 1;}
        gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);
        e->raw[0x08]=0x67;e->raw[0x09]=0x8C;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x20;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=8;e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[0x08]=0x91;e->raw[0x09]=0x8C;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=1;entity60_launch_toward_player(e);return 1;}
    if(st==0x0C){entity60_launch_toward_player(e);return 1;}
    if(st==0x0E){
        unsigned bad=0;uint8_t x=e->raw[0x11],y=e->raw[0x13];if(x<8u||x>=0x98u||y<8u||y>=0xF8u||e->raw[ENT_MOTION_PHASE]==0)bad=1;
        if(bad){e->raw[ENT_FLAGS]&=(uint8_t)~3u;gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x71u);e->raw[ENT_STATE]=0;}
        return 1;
    }
    return 1;
}


/* Type $3F / 63, bank-2 table $94A8.  This family walks normally, then
   performs four short ballistic hops selected from the original $8CA3
   records.  $420D is the already-lifted ballistic_update(). */
static int entity63_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(!entity_try_spawn_list(e,3u,1u))return 1;
        e->raw[ENT_FLAGS]|=1u;e->raw[0x08]=0x6A;e->raw[0x09]=0x8D;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;
        gaw_entity_set16(e,0x2E,0xFFE0u);e->raw[ENT_MOTION_PHASE]=0x30;e->raw[ENT_STATE]=2;return 1;
    }
    if(st==2){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x88;e->raw[0x09]=0x8D;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity53_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);
        if(r<2u){e->raw[ENT_STATE]=4;return 1;} if(r<8u || r!=8u){e->raw[ENT_STATE]=6;return 1;}
        gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0x10;e->raw[0x23]=e->raw[0x13];e->raw[0x27]=e->raw[0x11];e->raw[0x2C]=4;e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        const uint8_t *q=entity49_records+(unsigned)(gaw_platform_entropy8()&7u)*8u;uint8_t flags=q[4];
        if(e->raw[0x27]<0x31u && (flags&1u)) return 1;
        if(e->raw[0x27]>=0x80u && (flags&2u)) return 1;
        if(e->raw[0x23]<0x29u && (flags&4u)) return 1;
        if(e->raw[0x23]>=0xD8u && (flags&8u)) return 1;
        uint16_t d=entity_map_descriptor(e,(int8_t)q[6],(int8_t)q[5]);
        uint16_t d2=entity_map_descriptor(e,(int8_t)(q[6]+8u),(int8_t)q[5]);
        if((((uint8_t)(d>>8)|(uint8_t)(d2>>8))&0xE0u)!=0)return 1;
        gaw_entity_set16(e,0x20,u16le_at(q));gaw_entity_set16(e,0x24,u16le_at(q+2));e->raw[ENT_DIRECTION]=q[7];gaw_entity_set16(e,0x28,0x0210u);e->raw[ENT_STATE]=0x0C;ballistic_update(e);return 1;
    }
    if(st==0x0C){
        if(gaw_entity_get16(e,0x2A)!=0){ballistic_update(e);return 1;}
        e->raw[0x2C]=(uint8_t)(e->raw[0x2C]-1u);if(e->raw[0x2C]!=0){e->raw[ENT_STATE]=0x0A;return 1;}
        gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[0x08]=0x6A;e->raw[0x09]=0x8D;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=0x30;e->raw[ENT_STATE]=0x0E;return 1;
    }
    if(st==0x0E && e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)|0x70u);e->raw[ENT_STATE]=0;}
    return 1;
}

/* Type $41 / 65, table $96C1: blinking generator that emits two type-$1D
   auxiliaries in opposite horizontal directions. */
static int entity65_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){
        if(!entity_try_spawn_list(e,6u,1u))return 1;
        e->raw[ENT_FLAGS]&=(uint8_t)~1u;e->raw[0x08]=0x30;e->raw[0x09]=0x90;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;
        e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)|0x70u);e->raw[ENT_STATE]=2;return 1;
    }
    if(st==2){if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_FLAGS]|=1u;e->raw[ENT_MOTION_PHASE]=0x0Au;e->raw[ENT_STATE]=4;}return 1;}
    if(st==4 && e->raw[ENT_MOTION_PHASE]==0){
        e->raw[ENT_FLAGS]&=(uint8_t)~1u;
        for(int d=1;d>=0;--d){GawEntity *c=entity_spawn_aux_ptr(e,0x1Du);if(!c)break;c->raw[ENT_DIRECTION]=(uint8_t)d;}
        e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)|0x70u);e->raw[ENT_STATE]=0;
    }
    return 1;
}

/* Type $42 / 66, table $9726: fixed-position sinusoidal flyer. */
static int entity66_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[ENT_FLAGS]|=3u;e->raw[0x13]=0x80;e->raw[0x11]=0x51;e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]==3u){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x26]=e->raw[0x13];e->raw[0x28]=e->raw[0x11];e->raw[0x08]=0x42;e->raw[0x09]=0x8E;e->raw[ENT_ANIM_DELAY]=7;e->raw[ENT_ANIM_FRAMES]=2;gaw_entity_set16(e,0x21,0);gaw_entity_set16(e,0x23,0);e->raw[ENT_STATE]=4;}return 1;}
    if(st==4){
        if(e->raw[0x2A]!=0x60u) ++e->raw[0x2A];
        int16_t v=sine_scaled(e->raw[0x29],e->raw[0x2A],1);
        e->raw[0x13]=(uint8_t)(e->raw[0x26]+(uint8_t)((uint16_t)v>>8));
        if(e->raw[0x2B]!=0x38u) ++e->raw[0x2B];
        v=sine_scaled(e->raw[0x29],e->raw[0x2B],0);
        e->raw[0x11]=(uint8_t)(e->raw[0x28]+(uint8_t)((uint16_t)v>>8));
        e->raw[0x29]=(uint8_t)(e->raw[0x29]+1u);static const uint8_t face[4]={1,2,0,3};e->raw[ENT_DIRECTION]=face[((uint8_t)(e->raw[0x29]-0x20u)>>6)&3u];
        if(gaw_platform_entropy8()==0x7Fu){e->raw[0x08]=0x7E;e->raw[0x09]=0x8E;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_DIRECTION]=(gaw_ram_read8(PLAYER_Y_ADDR)>=e->raw[0x13])?3u:2u;if(gaw_ram_read8(PLAYER_Y_ADDR)<e->raw[0x13] && (uint8_t)(e->raw[0x13]-gaw_ram_read8(PLAYER_Y_ADDR))<0x30u)e->raw[ENT_DIRECTION]=0;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=0x18;}
        return 1;
    }
    if(st==6){if(e->raw[ENT_MOTION_PHASE]==0){(void)entity_spawn_aux(e,0x1Cu);e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=8;}return 1;}
    if(st==8 && e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0x42;e->raw[0x09]=0x8E;e->raw[ENT_ANIM_DELAY]=7;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}
    return 1;
}

/* Types $43-$45 / 67..69, table $9843. */
static int entity67_69_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity_try_spawn_list(e,0u,1u)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x02;e->raw[0x09]=0x91;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,type==67u?entity38_motion_fast:entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<4u){e->raw[ENT_STATE]=6;return 1;}
        entity_direction_toward_player_dominant(e);
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}load_motion_record(e,type==67u?entity38_motion_fast:entity32_motion);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A && e->raw[ENT_MOTION_PHASE]==0){
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION]) || (gaw_platform_entropy8()&0x0Fu)<10u){e->raw[ENT_STATE]=4;return 1;}
        e->raw[ENT_STATE]=6;if(type>=68u)(void)entity_spawn_aux(e,0x70u);
    }
    return 1;
}


/* $4A57: select one of the eight $8CA3 ballistic records, usually biased
   toward Arthur but occasionally fully random. */
static uint8_t entity_ballistic_record_toward_player(const GawEntity *e) {
    if((gaw_platform_entropy8()&0x0Fu)>=10u) return (uint8_t)(gaw_platform_entropy8()&7u);
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);
    unsigned dy=py>=e->raw[0x13]?(unsigned)(py-e->raw[0x13]):(unsigned)(e->raw[0x13]-py);
    unsigned dx=px>=e->raw[0x11]?(unsigned)(px-e->raw[0x11]):(unsigned)(e->raw[0x11]-px);
    if(dx>=dy){uint8_t q=(py>=e->raw[0x13])?1u:0u;return (uint8_t)(q+(px>=e->raw[0x11]?2u:0u));}
    {uint8_t q=(py>=e->raw[0x13])?6u:4u;return (uint8_t)(q+(px>=e->raw[0x11]?1u:0u));}
}
static int entity_ballistic_record_allowed(const GawEntity *e,const uint8_t *q) {
    uint8_t flags=q[4];
    if(e->raw[0x27]<0x31u && (flags&1u)) return 0;
    if(e->raw[0x27]>=0x80u && (flags&2u)) return 0;
    if(e->raw[0x23]<0x29u && (flags&4u)) return 0;
    if(e->raw[0x23]>=0xD8u && (flags&8u)) return 0;
    uint16_t d=entity_map_descriptor(e,(int8_t)q[6],(int8_t)q[5]);uint16_t d2=entity_map_descriptor(e,(int8_t)(q[6]+8u),(int8_t)q[5]);
    return ((((uint8_t)(d>>8)|(uint8_t)(d2>>8))&0xE0u)==0);
}
static void entity_start_ballistic_record(GawEntity *e,const uint8_t *q,uint8_t next_state) {
    gaw_entity_set16(e,0x20,u16le_at(q));gaw_entity_set16(e,0x24,u16le_at(q+2));e->raw[ENT_DIRECTION]=q[7];gaw_entity_set16(e,0x28,0x0210u);e->raw[ENT_STATE]=next_state;ballistic_update(e);
}

/* Type $46 / 70, bank-2 table $98FF. */
static int entity70_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_place_fixed(e);e->raw[0x08]=0xC2;e->raw[0x09]=0x91;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAME]=2;gaw_entity_set16(e,0x2E,0xFFE0u);e->raw[ENT_STATE]=2;return 1;}
    if(st==2){uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;if(dy<0x1Du&&dx<0x1Du){e->raw[ENT_ANIM_DELAY]=5;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_MOTION_PHASE]=0x18;e->raw[ENT_STATE]=4;}return 1;}
    if(st==4){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[0x08]=0xFD;e->raw[0x09]=0x91;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x0E;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x23]=e->raw[0x13];e->raw[0x27]=e->raw[0x11];e->raw[ENT_STATE]=6;return 1;}
    if(st==6){const uint8_t *q=entity49_records+(unsigned)entity_ballistic_record_toward_player(e)*8u;if(!entity_ballistic_record_allowed(e,q))return 1;entity_start_ballistic_record(e,q,8);return 1;}
    if(st==8){if(gaw_entity_get16(e,0x2A)!=0)ballistic_update(e);else e->raw[ENT_STATE]=6;return 1;}
    return 1;
}


static uint8_t entity71_edge_adjust(const GawEntity *e,uint8_t mode) {
    uint8_t x=(uint8_t)(e->raw[0x11]&0xF0u),y=(uint8_t)(e->raw[0x13]&0xF0u);
    switch(mode&7u){
        case 0: if(x<0x30u)mode=1;break;case 1:if(x>=0x70u)mode=0;break;
        case 2: if(y<0x50u)mode=3;break;case 3:if(y>=0xB0u)mode=2;break;
        case 4: if(y>=0xB0u||x<0x30u)mode=5;break;case 5:if(y<0x50u||x>=0x70u)mode=4;break;
        case 6: if(y<0x50u||x<0x30u)mode=7;break;default:if(y>=0xB0u||x>=0x70u)mode=6;break;
    }
    return mode;
}
static uint8_t entity71_choose_mode(GawEntity *e,uint8_t type) {
    static const uint8_t transitions[32]={0,0,6,4,1,1,5,7,2,2,5,6,3,3,4,7,4,4,0,3,5,5,2,1,6,6,0,2,7,7,1,3};
    uint8_t d;
    if(type<73u){uint8_t r=gaw_platform_entropy8();d=(r<0x20u)?(uint8_t)(r&7u):transitions[(unsigned)(e->raw[0x20]&7u)*4u+(r&3u)];}
    else{
        uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);
        if(py>=e->raw[0x13])d=(px>=e->raw[0x11])?7u:4u;else d=(px>=e->raw[0x11])?5u:6u;
    }
    return entity71_edge_adjust(e,d);
}
static void entity71_load_motion(GawEntity *e,uint8_t mode) {
    static const uint8_t rec[40]={
        0x00,0xFF,0x00,0x00,0, 0x00,0x01,0x00,0x00,1, 0x00,0x00,0x00,0xFF,2, 0x00,0x00,0x00,0x01,3,
        0x00,0xFF,0x00,0x01,3, 0x00,0x01,0x00,0xFF,2, 0x00,0xFF,0x00,0xFF,2, 0x00,0x01,0x00,0x01,3
    };
    mode&=7u;e->raw[0x20]=mode;e->raw[ENT_MOTION_PHASE]=8;const uint8_t *q=rec+(unsigned)mode*5u;
    e->raw[ENT_DELTA0]=q[0];e->raw[ENT_DELTA0+1]=q[1];e->raw[ENT_DELTA1]=q[2];e->raw[ENT_DELTA1+1]=q[3];e->raw[ENT_DIRECTION]=q[4];e->raw[ENT_STATE]=6;
}
static void entity71_begin_move(GawEntity *e,uint8_t type){entity71_load_motion(e,entity71_choose_mode(e,type));}

/* Types $47-$49 / 71..73, wrapper table at $4D3E. */
static int entity71_73_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity_try_spawn_list(e,0u,1u)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[0x08]=0x27;e->raw[0x09]=0x92;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x2E]=0x14;entity71_begin_move(e,type);return 1;
    }
    if(st==4){entity71_begin_move(e,type);return 1;}
    if(st==6){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(e->raw[0x2E]!=0){--e->raw[0x2E];entity71_begin_move(e,type);return 1;}
        if(original_random_byte()>=8u){entity71_begin_move(e,type);return 1;}gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[0x2F]=0x10;e->raw[ENT_STATE]=8;return 1;
    }
    if(st==8){
        if(--e->raw[0x2F]!=0) return 1;
        e->raw[ENT_ANIM_DELAY]=(uint8_t)(e->raw[ENT_ANIM_DELAY]+1u);
        if(e->raw[ENT_ANIM_DELAY]<0x0Au){e->raw[0x2F]=0x10;return 1;}if(e->raw[ENT_ANIM_FRAME]!=0){e->raw[0x2F]=0x10;return 1;}
        e->raw[0x2F]=0x40;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){
        if(type==73u && e->raw[0x2F]==0x20u) (void)entity_spawn_aux(e,0x14u);
        if(--e->raw[0x2F]!=0) return 1;
        e->raw[0x08]=0x27;e->raw[0x09]=0x92;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x2E]=0x14;entity71_begin_move(e,type);return 1;
    }
    return 1;
}


static int entity_choose_different_direction(GawEntity *e) {
    uint8_t d=(uint8_t)(gaw_platform_entropy8()&3u);if(d==(e->raw[ENT_DIRECTION]&3u))return 0;
    if(d==0u && e->raw[0x11]<0x31u) return 0;
    if(d==1u && e->raw[0x11]>=0x88u) return 0;
    if(d==2u && e->raw[0x13]<0x29u) return 0;
    if(d==3u && e->raw[0x13]>=0xD8u) return 0;
    e->raw[ENT_DIRECTION]=d;return 1;
}
static void entity74_75_state(GawEntity *e,uint8_t type) {
    static const uint8_t motion[17]={0x10,0x00,0xFF,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0xFF,0x00,0x00,0x00,0x01};
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity_try_spawn_list(e,0u,1u)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x51;e->raw[0x09]=0x92;e->raw[ENT_ANIM_DELAY]=5;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=(type==74u)?0u:1u;e->raw[ENT_STATE]=4;st=4;}
    if(st==4){if(!entity_choose_different_direction(e))return;load_motion_record(e,motion);e->raw[ENT_STATE]=6;return;}
    if(st==6){if(e->raw[ENT_MOTION_PHASE]!=0)return;if(!entity_direction_blocked(e,e->raw[ENT_DIRECTION]) && (gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=4;return;}gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=8;return;}
    if(st==8){if(e->raw[ENT_MOTION_PHASE]!=0)return;if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=4;return;}e->raw[ENT_MOTION_PHASE]=0x20;return;}
    if(st==0x0A){if(gaw_ram_read8(RAM_FRAME_COUNTER)!=e->raw[0x21])return;unsigned q=e->raw[0x22]&3u;static const int8_t xo[4]={-8,8,8,-8},yo[4]={8,8,-8,-8},vx[4]={-2,2,2,-2},vy[4]={2,2,-2,-2};uint16_t d=entity_map_descriptor(e,yo[q],xo[q]);if((((uint8_t)(d>>8))&0x80u)==0){e->raw[ENT_DELTA0+1]=(uint8_t)vx[q];e->raw[ENT_DELTA1+1]=(uint8_t)vy[q];}e->raw[ENT_MOTION_PHASE]=4;e->raw[ENT_STATE]=0x0C;return;}
    if(st==0x0C){if(e->raw[ENT_MOTION_PHASE]!=0)return;e->raw[ENT_DELTA0+1]=0;e->raw[ENT_DELTA1+1]=0;e->raw[ENT_STATE]=0x0E;return;}
    if(st==0x0E){if(e->raw[ENT_HIT_FLASH_TIMER]!=0)return;e->raw[ENT_FLAGS]|=2u;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x10u);e->raw[ENT_STATE]=6;}
}
static void entity74_75_split_after_hit(GawEntity *e) {
    uint8_t damage=e->raw[ENT_PENDING_DAMAGE];if(damage==0||e->raw[ENT_HP]<=damage||e->raw[0x20]==0)return;
    e->raw[0x20]=0;e->raw[0x22]=0;e->raw[ENT_DELTA0]=e->raw[ENT_DELTA0+1]=e->raw[ENT_DELTA1]=e->raw[ENT_DELTA1+1]=0;e->raw[ENT_ANIM_FRAME]=e->raw[ENT_ANIM_FRAMES]=e->raw[ENT_ANIM_DELAY]=0;e->raw[0x08]=0x7B;e->raw[0x09]=0x92;e->raw[0x21]=(uint8_t)(gaw_ram_read8(RAM_FRAME_COUNTER)+1u);e->raw[ENT_STATE]=0x0A;e->raw[ENT_FLAGS]&=(uint8_t)~2u;
    uint8_t clone=3;for(unsigned i=16;i<32 && clone!=0;++i){GawEntity *c=gaw_entity(i);if(c->raw[ENT_TYPE]!=0)continue;memcpy(c->raw,e->raw,0x22u);c->raw[0x22]=clone--;}
}
/* Types $4A-$4B / 74..75, wrapper $4F44 + bank-2 table $9A1B. */
static int entity74_75_handler(GawEntity *e,uint8_t type){entity74_75_state(e,type);entity74_75_split_after_hit(e);return 1;}


/* Type $4C / 76, wrapper $4FB1 -> bank-2 table $9B1E. */
static int entity76_handler(GawEntity *e) {
    static const uint8_t rec[48]={
        0x05,0x00,0xF0,0xFC,0x80,0xFF, 0x09,0x00,0xF0,0xFC,0x80,0x00,
        0x06,0x01,0xF0,0xFE,0x80,0xFF, 0x0A,0x01,0xF0,0xFE,0x80,0x00,
        0x05,0x02,0x70,0xFD,0x00,0xFF, 0x06,0x02,0x70,0xFE,0x00,0xFF,
        0x09,0x03,0x70,0xFD,0x00,0x01, 0x0A,0x03,0x70,0xFE,0x00,0x01
    };
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(entity_try_spawn_list(e,0u,1u)){e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x51;e->raw[0x09]=0x92;e->raw[ENT_ANIM_DELAY]=5;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=1;e->raw[ENT_STATE]=4;st=4;}
    if(st==4){gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x1Fu)|0x60u);e->raw[ENT_STATE]=6;return 1;}
    if(st==6){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        e->raw[ENT_MOTION_PHASE]=0x20;unsigned ri=(unsigned)(gaw_platform_entropy8()&0x0Eu)>>1;const uint8_t *q=rec+ri*6u;uint8_t flags=q[0],x=e->raw[0x11],y=e->raw[0x13];
        if((flags&1u)&&x<0x41u) return 1;
        if((flags&2u)&&x>=0x80u) return 1;
        if((flags&4u)&&y<0x39u) return 1;
        if((flags&8u)&&y>=0xC8u) return 1;
        e->raw[ENT_DIRECTION]=q[1];e->raw[ENT_DELTA0]=q[2];e->raw[ENT_DELTA0+1]=q[3];e->raw[ENT_DELTA1]=q[4];e->raw[ENT_DELTA1+1]=q[5];
        if(gaw_ram_read8(RAM_ENTITY_SLOT_INDEX)<0x18u){unsigned slot=24u+((gaw_ram_read8(RAM_FRAME_COUNTER)&0x0Eu)>>1);GawEntity *c=gaw_entity(slot);if(c->raw[ENT_TYPE]==0){e->raw[ENT_STATE]=4;memcpy(c->raw,e->raw,0x20u);e->raw[ENT_STATE]=8;return 1;}}
        e->raw[ENT_STATE]=8;return 1;
    }
    if(st==8){gaw_entity_set16(e,ENT_DELTA0,(uint16_t)(gaw_entity_get16(e,ENT_DELTA0)+0x20u));if(e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=4;return 1;}
    return 1;
}



/* $3F07: select one of eight direction/vector records from Arthur's dominant
   relative octant.  The original C register starts at 2, encodes the signs
   of Y/X in bits 2/1, then increments when |dx| < |dy|. */
static uint8_t entity_octant_toward_player(const GawEntity *e) {
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR),c=2u;
    unsigned dy=py>=e->raw[0x13]?(unsigned)(py-e->raw[0x13]):(unsigned)(e->raw[0x13]-py);
    if(py<e->raw[0x13]) c|=4u;
    unsigned dx=px>=e->raw[0x11]?(unsigned)(px-e->raw[0x11]):(unsigned)(e->raw[0x11]-px);
    if(px<e->raw[0x11]) c&=(uint8_t)~2u;
    if(dx<dy) ++c;
    return (uint8_t)(c&7u);
}
static void entity_load_octant_vector(GawEntity *e,const uint8_t *records) {
    static const uint8_t dir[8]={0,3,1,3,0,2,1,2};
    uint8_t q=entity_octant_toward_player(e);const uint8_t *r=records+(unsigned)q*4u;
    e->raw[ENT_DIRECTION]=dir[q];
    e->raw[ENT_DELTA1]=r[0];e->raw[ENT_DELTA1+1]=r[1];
    e->raw[ENT_DELTA0]=r[2];e->raw[ENT_DELTA0+1]=r[3];
}
static void entity_spawn_intro_984f(GawEntity *e) {
    if(!entity_try_spawn_list(e,0u,1u)) return;
    e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;
}

/* Types $4D-$4E / 77..78, wrapper $4FB7 + bank-2 table $9C02. */
static void entity77_load_mode(GawEntity *e,uint8_t mode) {
    static const uint8_t vec[32]={
        0x7A,0x00,0xD9,0xFE, 0x27,0x01,0x86,0xFF, 0x7A,0x00,0x27,0x01, 0x27,0x01,0x7A,0x00,
        0x86,0xFF,0xD9,0xFE, 0xD9,0xFE,0x86,0xFF, 0x86,0xFF,0x27,0x01, 0xD9,0xFE,0x7A,0x00
    };
    static const uint8_t dir[8]={0,3,1,3,0,2,1,2};
    mode&=7u;e->raw[0x20]=mode;const uint8_t *q=vec+(unsigned)mode*4u;
    e->raw[ENT_DELTA1]=q[0];e->raw[ENT_DELTA1+1]=q[1];e->raw[ENT_DELTA0]=q[2];e->raw[ENT_DELTA0+1]=q[3];
    e->raw[ENT_DIRECTION]=dir[mode];e->raw[0x21]=0x80;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=0x20;
}
static uint8_t entity77_bounce_mode(uint8_t edge,uint8_t r) {
    static const uint8_t choices[16]={3,6,2,7, 4,0,5,1, 0,3,1,2, 5,4,7,6};
    return choices[(unsigned)(edge&3u)*4u+((r&0x0Fu)>>2)];
}
static int entity77_78_handler(GawEntity *e,uint8_t type) {
    static const uint8_t vec[32]={
        0x7A,0x00,0xD9,0xFE, 0x27,0x01,0x86,0xFF, 0x7A,0x00,0x27,0x01, 0x27,0x01,0x7A,0x00,
        0x86,0xFF,0xD9,0xFE, 0xD9,0xFE,0x86,0xFF, 0x86,0xFF,0x27,0x01, 0xD9,0xFE,0x7A,0x00
    };
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]==3u){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x8B;e->raw[0x09]=0x92;e->raw[ENT_ANIM_DELAY]=1;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}return 1;}
    if(st==4){
        uint8_t mode=(uint8_t)(gaw_platform_entropy8()&7u);
        if(type==78u && (gaw_platform_entropy8()&0x0Fu)<8u){entity_load_octant_vector(e,vec);e->raw[0x21]=0x80;e->raw[ENT_STATE]=6;e->raw[ENT_MOTION_PHASE]=0x20;}
        else entity77_load_mode(e,mode);
        return 1;
    }
    if(st==6){
        uint8_t edge=0xFFu;
        if(e->raw[0x11]<0x28u)edge=0u;else if(e->raw[0x11]>=0x90u)edge=1u;else if(e->raw[0x13]<0x28u)edge=2u;else if(e->raw[0x13]>=0xD8u)edge=3u;
        else {if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(--e->raw[0x21]!=0){e->raw[ENT_MOTION_PHASE]=0x20;return 1;}edge=e->raw[ENT_DIRECTION]&3u;}
        entity77_load_mode(e,entity77_bounce_mode(edge,gaw_platform_entropy8()));return 1;
    }
    return 1;
}
static void entity77_wrapper_resource(GawEntity *e) {
    if((e->raw[ENT_FLAGS]&4u)==0) return;
    uint8_t v=gaw_ram_read8(0xC0DBu);
    gaw_ram_write8(0xC0DBu,v>=8u?(uint8_t)(v-8u):0u);
    e->raw[ENT_FLAGS]&=(uint8_t)~4u;
}

/* Types $4F-$51 / 79..81, wrapper $4FD2 + bank-2 table $9DA6. */
static int entity79_81_handler(GawEntity *e,uint8_t type) {
    static const uint8_t charge[17]={0x08,0x00,0xFF,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0xFF,0x00,0x00,0x00,0x01};
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xB5;e->raw[0x09]=0x92;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=6;return 1;}entity_direction_toward_player_dominant(e);
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if(type==80u){if(!entity_direction_toward_player_aligned(e)){e->raw[ENT_STATE]=6;return 1;}if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[0x2C]=0x10;e->raw[ENT_STATE]=0x0A;return 1;}
        load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){
        if(type==79u){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[ENT_STATE]=entity_direction_blocked(e,e->raw[ENT_DIRECTION])?4u:6u;return 1;}
        if(type==80u){load_motion_record(e,charge);e->raw[ENT_STATE]=0x0C;return 1;}
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<4u) (void)entity_spawn_aux(e,0x18u);
        e->raw[ENT_STATE]=6;return 1;
    }
    if(st==0x0C && type==80u){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}if(--e->raw[0x2C]==0)e->raw[ENT_STATE]=4;else e->raw[ENT_STATE]=0x0A;return 1;}
    return 1;
}



/* Type $52 / 82, wrapper $4FD8 + bank-2 table $9EA5. */
static int entity82_handler(GawEntity *e) {
    static const uint8_t vectors[32]={
        0x3D,0x00,0x6D,0xFF, 0x93,0x00,0xC3,0xFF, 0x3D,0x00,0x93,0x00, 0x93,0x00,0x3D,0x00,
        0xC3,0xFF,0x6D,0xFF, 0x6D,0xFF,0xC3,0xFF, 0xC3,0xFF,0x93,0x00, 0x6D,0xFF,0x3D,0x00
    };
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){if(gaw_ram_read8(0xC052u)!=0 && gaw_ram_read8(0xC054u)!=0)return 1;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(!entity_try_spawn_list(e,0u,1u))return 1;e->raw[0x08]=0x45;e->raw[0x09]=0x93;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=3;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(e->raw[ENT_ANIM_FRAME]!=2u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x6B;e->raw[0x09]=0x93;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=6;return 1;}
    if(st==6){entity_load_octant_vector(e,vectors);e->raw[ENT_STATE]=8;e->raw[ENT_MOTION_PHASE]=0x20;return 1;}
    if(st==8){
        if(e->raw[0x11]<0x10u||e->raw[0x11]>=0x90u||e->raw[0x13]<0x10u||e->raw[0x13]>=0xF0u){e->raw[ENT_STATE]=6;return 1;}
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if((gaw_platform_entropy8()&0x0Fu)>=4u){e->raw[ENT_STATE]=6;return 1;}
        gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0x48;e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=6;
    return 1;
}

/* Type $53 / 83, wrapper $4FF3 + bank-2 table $9F81. */
static int entity83_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xFB;e->raw[0x09]=0x93;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;}
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=6;return 1;}entity_direction_toward_player_dominant(e);
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=entity_direction_blocked(e,e->raw[ENT_DIRECTION])?4u:6u;
    return 1;
}
static void entity83_wrapper_hud(GawEntity *e) {if(e->raw[ENT_FLAGS]&4u){gaw_ram_write8(0xC0BFu,1u);e->raw[ENT_FLAGS]&=(uint8_t)~4u;}}



/* Types $54-$55 / 84..85, wrapper $5008 + bank-2 table $9FFC. */
static void entity84_idle_reset(GawEntity *e) {
    e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_ANIM_FRAME]=0;
    e->raw[0x08]=0x8B;e->raw[0x09]=0x94;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x71u);e->raw[ENT_STATE]=6;
}
static int entity84_85_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_place_fixed(e);e->raw[0x08]=0xFA;e->raw[0x09]=0x84;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_STATE]=4;st=4;}
    if(st==4){entity84_idle_reset(e);return 1;}
    if(st==6){
        if(type==85u){if(!entity_direction_toward_player_aligned(e))return 1;}
        else {if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if((gaw_platform_entropy8()&0x0Fu)>=2u){e->raw[ENT_MOTION_PHASE]=0x20;return 1;}}
        e->raw[0x08]=0xD7;e->raw[0x09]=0x94;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=8;e->raw[ENT_STATE]=8;return 1;
    }
    if(st==8){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(type!=85u)e->raw[ENT_DIRECTION]=(uint8_t)(gaw_platform_entropy8()&3u);e->raw[ENT_MOTION_PHASE]=8;e->raw[ENT_STATE]=0x0A;return 1;}
    if(st==0x0A){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if((gaw_platform_entropy8()&0x0Fu)<4u){entity84_idle_reset(e);return 1;}
        (void)entity_spawn_aux(e,0x71u);
        if(type==85u || (gaw_platform_entropy8()&0x0Fu)<4u){entity84_idle_reset(e);return 1;}
        e->raw[ENT_MOTION_PHASE]=0x80;e->raw[ENT_STATE]=8;return 1;
    }
    return 1;
}



/* $5020: face Arthur on the dominant axis, without the map-block test used
   by $4A15. */
static void entity_face_player_dominant(GawEntity *e) {
    uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);
    unsigned dx=px>=e->raw[0x11]?(unsigned)(px-e->raw[0x11]):(unsigned)(e->raw[0x11]-px);
    unsigned dy=py>=e->raw[0x13]?(unsigned)(py-e->raw[0x13]):(unsigned)(e->raw[0x13]-py);
    uint8_t hd=(px>=e->raw[0x11])?1u:0u,vd=(py>=e->raw[0x13])?3u:2u;
    e->raw[ENT_DIRECTION]=(dy>=dx)?vd:hd;
}

/* Type $56 / 86, wrapper $500E + table $A0E6. */
static int entity86_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[ENT_FLAGS]&=(uint8_t)~1u;if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(!entity_try_spawn_list(e,0u,1u))return 1;e->raw[0x08]=0xD7;e->raw[0x09]=0x94;e->raw[ENT_HIT_FLASH_TIMER]=0x20;e->raw[ENT_FLAGS]&=(uint8_t)~2u;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[ENT_FLAGS]|=2u;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;(void)entity_spawn_aux(e,0x71u);e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_STATE]=6;return 1;}
    if(st==6){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[ENT_MOTION_PHASE]=0x10;e->raw[ENT_HIT_FLASH_TIMER]=0x10;e->raw[ENT_FLAGS]&=(uint8_t)~2u;e->raw[ENT_STATE]=8;return 1;}
    if(st==8 && e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x68u);e->raw[ENT_STATE]=0;}
    return 1;
}

/* Types $59-$5A / 89..90, wrapper $501A + table $A29A.  Their last two
   states deliberately reuse the type-86 $A13E/$A15F handlers. */
static int entity89_90_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[ENT_FLAGS]&=(uint8_t)~1u;if(e->raw[ENT_MOTION_PHASE]!=0)return 1;if(!entity_try_spawn_list(e,0u,1u))return 1;e->raw[0x08]=0xAA;e->raw[0x09]=0x95;e->raw[ENT_FLAGS]&=(uint8_t)~2u;e->raw[ENT_HIT_FLASH_TIMER]=0x20;e->raw[ENT_STATE]=2;entity_face_player_dominant(e);return 1;}
    if(st==2){if(e->raw[ENT_HIT_FLASH_TIMER]!=0)return 1;e->raw[0x08]=0xF6;e->raw[0x09]=0x95;e->raw[ENT_FLAGS]|=2u;e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&7u)+0x28u);e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;(void)entity_spawn_aux(e,0x17u);e->raw[ENT_MOTION_PHASE]=(uint8_t)((gaw_platform_entropy8()&3u)+0x18u);e->raw[ENT_STATE]=6;return 1;}
    if(st==6){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;e->raw[ENT_MOTION_PHASE]=(type==90u)?8u:0x10u;e->raw[ENT_HIT_FLASH_TIMER]=0x10;e->raw[ENT_FLAGS]&=(uint8_t)~2u;e->raw[ENT_STATE]=8;return 1;}
    if(st==8 && e->raw[ENT_MOTION_PHASE]==0){uint8_t t=(uint8_t)((gaw_platform_entropy8()&0x0Fu)+0x68u);if(type==90u)t=(uint8_t)(t-0x20u);e->raw[ENT_MOTION_PHASE]=t;e->raw[ENT_STATE]=0;}
    return 1;
}



/* Types $57-$58 / 87..88, wrapper $5014 + table $A181. */
static int entity87_88_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_place_fixed(e);e->raw[0x08]=0x67;e->raw[0x09]=0x95;e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_FLAGS]&=(uint8_t)~3u;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){
        uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;
        if(dy<0x18u&&dx<0x18u){e->raw[ENT_FLAGS]|=1u;e->raw[ENT_HIT_FLASH_TIMER]=0x20;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=0x0A;}return 1;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=6;return 1;}entity_direction_toward_player_dominant(e);
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}load_motion_record(e,entity42_motion);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        e->raw[ENT_FLAGS]|=2u;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if(type==88u && (gaw_platform_entropy8()&0x0Fu)<2u){e->raw[0x08]=0x91;e->raw[0x09]=0x95;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_ANIM_FRAME]=0;gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0x80;e->raw[ENT_STATE]=0x0C;return 1;}
        e->raw[ENT_STATE]=6;return 1;
    }
    if(st==0x0C && e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0x67;e->raw[0x09]=0x95;e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;}
    return 1;
}



/* Type $5B / 91, wrapper $5043 + table $A302. */
static int entity91_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){
        if(e->raw[ENT_ANIM_FRAME]!=3u) return 1;
        e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x42;e->raw[0x09]=0x96;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=0;e->raw[0x21]=0x10;e->raw[ENT_STATE]=4;st=4;
    }
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=6;return 1;}entity_direction_toward_player_dominant(e);
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A){
        uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;
        if(dy<9u&&dx<9u&&gaw_ram_read8(0xC301u)!=0x0Cu){e->raw[0x08]=0x6C;e->raw[0x09]=0x96;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0;e->raw[ENT_STATE]=0x0C;return 1;}
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        e->raw[ENT_STATE]=entity_direction_blocked(e,e->raw[ENT_DIRECTION])?4u:6u;return 1;
    }
    if(st==0x0C){
        if(gaw_ram_read8(0xC318u)==0){e->raw[0x11]=(uint8_t)(e->raw[0x11]-8u);e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x42;e->raw[0x09]=0x96;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=0;e->raw[0x21]=0x10;e->raw[ENT_STATE]=4;if(entity_choose_random_direction(e)){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;}return 1;}
        e->raw[0x11]=(uint8_t)(gaw_ram_read8(PLAYER_X_ADDR)+8u);uint8_t d=(uint8_t)((gaw_ram_read8(0xC02Fu)&2u)-1u);e->raw[0x13]=(uint8_t)(gaw_ram_read8(PLAYER_Y_ADDR)+d);
        if(gaw_ram_read8(0xC304u)==0){gaw_ram_write8(0xC301u,0x0Cu);gaw_ram_write8(0xC30Bu,0);}
        if(--e->raw[0x21]==0){e->raw[0x21]=0x10;uint8_t v=gaw_ram_read8(0xC0DDu);if(v){gaw_ram_write8(0xC0DDu,(uint8_t)(v-1u));gaw_ram_write8(0xDE08u,0x95u);}}
        if((gaw_ram_read8(0xC021u)&0x0Fu)==0) return 1;
        if(++e->raw[0x20]<6u) return 1;
        gaw_ram_write8(0xC301u,0);e->raw[0x11]=(uint8_t)(e->raw[0x11]-8u);e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x42;e->raw[0x09]=0x96;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=0;e->raw[0x21]=0x10;e->raw[ENT_STATE]=4;if(entity_choose_random_direction(e)){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=8;}return 1;
    }
    return 1;
}

/* Types $5C-$5D / 92..93, wrapper $5049 + table $A421. */
static int entity92_93_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x85;e->raw[0x09]=0x96;e->raw[ENT_ANIM_DELAY]=0x0A;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;st=4;}
    if(st==4){if(!entity_choose_random_direction(e))return 1;e->raw[ENT_STATE]=6;st=6;}
    if(st==6){load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(type==92u){
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);if(r<2u){e->raw[ENT_STATE]=4;return 1;}if(r<8u){e->raw[ENT_STATE]=6;return 1;}e->raw[ENT_STATE]=entity_direction_toward_player_aligned(e)?4u:6u;return 1;
        }
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}if((gaw_platform_entropy8()&0x0Fu)<2u){e->raw[ENT_STATE]=6;return 1;}entity_direction_toward_player_dominant(e);if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=0x0A;return 1;
    }
    if(st==0x0A && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=entity_direction_blocked(e,e->raw[ENT_DIRECTION])?4u:6u;
    return 1;
}
static void entity92_93_wrapper_damage(GawEntity *e) {
    static const uint8_t required[4]={1,0,3,2};if(gaw_ram_read8(0xC30Au)!=required[e->raw[ENT_DIRECTION]&3u])e->raw[ENT_PENDING_DAMAGE]=0;
}



/* Type $5E / 94, wrapper $5059 + table $A50B. */
static int entity94_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_place_fixed(e);e->raw[0x08]=0x15;e->raw[0x09]=0x97;e->raw[ENT_FLAGS]&=(uint8_t)~3u;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(gaw_ram_read8(0xC052u)!=0&&gaw_ram_read8(0xC054u)!=0)return 1;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){(void)entity_spawn_aux(e,0x77u);e->raw[ENT_MOTION_PHASE]=0x30;e->raw[ENT_STATE]=6;return 1;}
    if(st==6 && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=2;
    return 1;
}
static void entity95_attack_start(GawEntity *e) {
    gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x0B;e->raw[ENT_ANIM_FRAMES]=4;e->raw[0x08]=0xD9;e->raw[0x09]=0x97;e->raw[ENT_STATE]=0x0A;
}
/* Types $5F-$60 / 95..96, wrapper $505F + table $A566. */
static int entity95_96_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_spawn_intro_984f(e);return 1;}
    if(st==2){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x49;e->raw[0x09]=0x97;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;return 1;}
    if(st==4){if(entity_choose_random_direction(e))e->raw[ENT_STATE]=6;return 1;}
    if(st==6){load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=8;return 1;}
    if(st==8){
        if(e->raw[ENT_MOTION_PHASE]!=0)return 1;
        if(type==95u){
            if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}if((gaw_platform_entropy8()&0x0Fu)<6u){e->raw[ENT_STATE]=6;return 1;}
            uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;
            if(dy>=0x18u){e->raw[ENT_STATE]=4;return 1;}if(dx>=0x18u){e->raw[ENT_STATE]=6;return 1;}entity95_attack_start(e);return 1;
        }
        if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}entity_direction_toward_player_dominant(e);if(entity_direction_blocked(e,e->raw[ENT_DIRECTION])){e->raw[ENT_STATE]=4;return 1;}
        uint8_t py=gaw_ram_read8(PLAYER_Y_ADDR),px=gaw_ram_read8(PLAYER_X_ADDR);unsigned dy=py>=e->raw[0x13]?py-e->raw[0x13]:e->raw[0x13]-py,dx=px>=e->raw[0x11]?px-e->raw[0x11]:e->raw[0x11]-px;
        if(dy<0x18u&&dx<0x18u){entity95_attack_start(e);return 1;}load_motion_record(e,entity32_motion);e->raw[ENT_STATE]=0x0C;return 1;
    }
    if(st==0x0A){if(e->raw[ENT_ANIM_FRAME]!=3u)return 1;static const uint8_t opposite[4]={1,0,3,2};e->raw[ENT_DIRECTION]=opposite[e->raw[ENT_DIRECTION]&3u];e->raw[0x08]=0x49;e->raw[0x09]=0x97;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;return 1;}
    if(st==0x0C && e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=entity_direction_blocked(e,e->raw[ENT_DIRECTION])?4u:6u;
    return 1;
}



/* Types $61-$62 / 97..98, wrapper $5065 + table $A6C7. */
static int entity97_98_handler(GawEntity *e,uint8_t type) {
    static const uint8_t motion[17]={0x04,0x00,0xFE,0x00,0x00,0x00,0x02,0x00,0x00,0x00,0x00,0x00,0xFE,0x00,0x00,0x00,0x02};
    static const uint8_t turn[4]={1,0,3,2};uint8_t st=e->raw[ENT_STATE];
    if(st==0){entity_place_fixed(e);e->raw[0x08]=0x55;e->raw[0x09]=0x98;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){e->raw[0x08]=0x55;e->raw[0x09]=0x98;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_DIRECTION]=(type==98u)?1u:3u;load_motion_record(e,motion);e->raw[ENT_STATE]=6;return 1;}
    if(st==4){load_motion_record(e,motion);e->raw[ENT_STATE]=6;return 1;}
    if(st==6 && e->raw[ENT_MOTION_PHASE]==0){if(entity_direction_blocked(e,e->raw[ENT_DIRECTION]) || ++e->raw[0x20]==0x60u){e->raw[0x20]=0;e->raw[ENT_DIRECTION]=turn[e->raw[ENT_DIRECTION]&3u];}e->raw[ENT_STATE]=4;}
    return 1;
}



/* Types $63/$64/$78/$79 (99,100,120,121), wrapper $506B + table $A754. */
static int entity99_family_handler(GawEntity *e,uint8_t type) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[ENT_FLAGS]|=3u;e->raw[0x08]=0x13;e->raw[0x09]=0x99;e->raw[ENT_DIRECTION]=1;e->raw[ENT_ANIM_DELAY]=0x28;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x20]=5;e->raw[0x21]=0;e->raw[0x13]=0x80;e->raw[0x11]=0x28;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_STATE]=2;return 1;}
    if(st==2){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=6;return 1;}
    if(st==4){load_motion_record(e,entity38_motion_fast);e->raw[ENT_STATE]=6;return 1;}
    if(st==6){
        if(e->raw[ENT_MOTION_PHASE]!=0) return 1;
        e->raw[ENT_STATE]=4;
        if((e->raw[ENT_DIRECTION]&1u)!=0){--e->raw[0x21];if(++e->raw[0x20]==5u)e->raw[ENT_DIRECTION]=1u;}else{--e->raw[0x20];if(++e->raw[0x21]==5u)e->raw[ENT_DIRECTION]=0u;}
        if((gaw_platform_entropy8()&0x0Fu)>=4u) return 1;
        e->raw[ENT_STATE]=8;
        if(type==100u && (gaw_platform_entropy8()&0x0Fu)<0x0Du){e->raw[0x08]=0xB9;e->raw[0x09]=0x99;e->raw[ENT_STATE]=0x0A;}else{e->raw[0x08]=0x7F;e->raw[0x09]=0x99;}
        gaw_entity_set16(e,ENT_DELTA0,0);e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_MOTION_PHASE]=0x20;return 1;
    }
    if(st==8){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;for(unsigned b=0;b<3u;++b)(void)entity_spawn_aux(e,0x72u);e->raw[0x08]=0x13;e->raw[0x09]=0x99;e->raw[ENT_ANIM_DELAY]=0x28;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;return 1;}
    if(st==0x0A){if(e->raw[ENT_MOTION_PHASE]!=0)return 1;for(int b=5;b>0;--b){GawEntity*c=entity_spawn_aux_ptr(e,0x73u);if(!c)break;c->raw[ENT_DIRECTION]=(uint8_t)(b-1);}e->raw[0x08]=0x13;e->raw[0x09]=0x99;e->raw[ENT_ANIM_DELAY]=0x28;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=4;return 1;}
    return 1;
}



/* Type $66 / 102, direct bank-1 handler $512B: child orbit/offset entity tied
   to the parent record at $C600. */
static int entity102_handler(GawEntity *e) {
    if(e->raw[ENT_STATE]==0){e->raw[ENT_FLAGS]|=0x23u;e->raw[0x08]=0x4A;e->raw[0x09]=0x9A;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_HP]=0x0C;e->raw[ENT_ATTACK]=0x0A;e->raw[ENT_STATE]=2;}
    e->raw[ENT_FLAGS]|=3u;uint8_t px=gaw_ram_read8(0xC611u),py=gaw_ram_read8(0xC613u);e->raw[0x11]=(uint8_t)(px+e->raw[0x21]);e->raw[0x13]=(uint8_t)(py+e->raw[0x20]);
    if(e->raw[0x11]<0x11u||e->raw[0x11]>=0x98u||e->raw[0x13]<0x19u||e->raw[0x13]>=0xE8u)e->raw[ENT_FLAGS]&=(uint8_t)~3u;
    return 1;
}



/* Type $65 / 101, wrapper $5071 + bank-2 table $A86D.  This is the
   controller for the eight type-102 orbit children in slots 24..31. */
static void entity101_boundary_correct(GawEntity *e) {
    uint8_t d=(uint8_t)(e->raw[0x20]&7u), x=(uint8_t)(e->raw[0x11]&0xF0u), y=(uint8_t)(e->raw[0x13]&0xF0u);
    switch(d){
        case 0: if(x<0x30u)e->raw[0x20]=1; break;
        case 1: if(x>=0x70u)e->raw[0x20]=0; break;
        case 2: if(y<0x50u)e->raw[0x20]=3; break;
        case 3: if(y>=0xB0u)e->raw[0x20]=2; break;
        case 4: if(y<0x50u || x>=0x70u)e->raw[0x20]=4; break;
        case 5: if(y>=0xB0u || x<0x30u)e->raw[0x20]=5; break;
        case 6: if(y>=0xB0u || x>=0x70u)e->raw[0x20]=6; break;
        case 7: if(y<0x50u || x<0x30u)e->raw[0x20]=7; break;
    }
}
static uint8_t entity101_choose_mode(const GawEntity *e) {
    /* $4EB7 for types >= $49: wait for an odd refresh sample, then choose
       the quadrant facing Arthur.  The portable entropy source replaces R. */
    uint8_t r;
    do { r=gaw_platform_entropy8(); } while((r&1u)==0u);
    (void)r;
    uint8_t d=6u, py=gaw_ram_read8(PLAYER_Y_ADDR), px=gaw_ram_read8(PLAYER_X_ADDR);
    if(py>=e->raw[0x13]){d=4u;if(px>=e->raw[0x11])d=7u;}
    else if(px>=e->raw[0x11])d=5u;
    return d;
}
static void entity101_load_motion(GawEntity *e) {
    static const uint8_t slow[41]={
        0x08, 0x00,0xFF,0x00,0x00,0x00, 0x00,0x01,0x00,0x00,0x01, 0x00,0x00,0xFF,0x02,0x00,
        0x00,0x00,0x01,0x03,0x00, 0xFF,0x00,0x01,0x03,0x00, 0x01,0x00,0xFF,0x02,0x00,
        0xFF,0x00,0xFF,0x02,0x00, 0x01,0x00,0x01,0x00,0x00
    };
    static const uint8_t fast[41]={
        0x10, 0x80,0xFF,0x00,0x00,0x00, 0x80,0x00,0x00,0x00,0x01, 0x00,0x00,0x80,0xFF,0x02,
        0x00,0x00,0x80,0x00,0x03, 0x80,0xFF,0x80,0x00,0x03, 0x80,0x00,0x80,0xFF,0x02,
        0x80,0xFF,0x80,0xFF,0x02, 0x80,0x00,0x80,0x00,0x00
    };
    const uint8_t *t=e->raw[0x2B]?fast:slow;uint8_t d=(uint8_t)(e->raw[0x20]&7u);const uint8_t *q=t+1u+(unsigned)d*5u;
    e->raw[ENT_MOTION_PHASE]=t[0];e->raw[ENT_DELTA0]=q[0];e->raw[ENT_DELTA0+1]=q[1];e->raw[ENT_DELTA1]=q[2];e->raw[ENT_DELTA1+1]=q[3];e->raw[ENT_DIRECTION]=q[4];
}
static uint8_t entity101_sine_hi(uint8_t phase,uint8_t radius,int quarter) {
    return (uint8_t)((uint16_t)sine_scaled(phase,radius,quarter)>>8);
}
static void entity101_update_orbit(GawEntity *e) {
    unsigned alive=0;for(unsigned i=0;i<8u;++i)if(gaw_ram_read8((uint16_t)(0xC780u+i*GAW_ENTITY_SIZE))!=0)++alive;
    e->raw[0x2B]=(uint8_t)alive;
    e->raw[ENT_FLAGS]&=(uint8_t)~2u;if(alive==0)e->raw[ENT_FLAGS]|=2u;
    uint8_t radius=e->raw[0x28];
    if(e->raw[0x2A]==0){if(++radius>=0x20u)e->raw[0x2A]=1u;else e->raw[0x28]=radius;}
    else {if(--radius<0x10u)e->raw[0x2A]=0u;else e->raw[0x28]=radius;}
    e->raw[0x29]=(uint8_t)(e->raw[0x29]+(alive>=4u?2u:4u));
    uint8_t a=e->raw[0x29],r=e->raw[0x28];
    uint8_t x=entity101_sine_hi(a,r,1),y=entity101_sine_hi(a,r,0),xn=(uint8_t)(0u-x),yn=(uint8_t)(0u-y);
    gaw_ram_write8(0xC7A0u,x);gaw_ram_write8(0xC8C1u,x);gaw_ram_write8(0xC801u,xn);gaw_ram_write8(0xC860u,xn);
    gaw_ram_write8(0xC7A1u,y);gaw_ram_write8(0xC800u,y);gaw_ram_write8(0xC861u,yn);gaw_ram_write8(0xC8C0u,yn);
    a=(uint8_t)(a+0x20u);x=entity101_sine_hi(a,r,1);y=entity101_sine_hi(a,r,0);xn=(uint8_t)(0u-x);yn=(uint8_t)(0u-y);
    gaw_ram_write8(0xC7D0u,x);gaw_ram_write8(0xC8F1u,x);gaw_ram_write8(0xC890u,xn);gaw_ram_write8(0xC831u,xn);
    gaw_ram_write8(0xC7D1u,y);gaw_ram_write8(0xC830u,y);gaw_ram_write8(0xC891u,yn);gaw_ram_write8(0xC8F0u,yn);
}
static int entity101_handler(GawEntity *e) {
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[ENT_FLAGS]|=1u;e->raw[0x13]=0x80;e->raw[0x11]=0x50;e->raw[0x08]=0x02;e->raw[0x09]=0x9A;e->raw[0x2B]=8;e->raw[ENT_HIT_FLASH_TIMER]=0x30;e->raw[ENT_STATE]=2;}
    else if(st==2){if(e->raw[ENT_HIT_FLASH_TIMER]==0){for(unsigned i=0;i<8u;++i){GawEntity*c=gaw_entity(24u+i);c->raw[ENT_TYPE]=102;c->raw[0x29]=(uint8_t)((7u-i)*0x20u);}e->raw[ENT_ANIM_DELAY]=2;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x28]=0;e->raw[0x2A]=0;e->raw[ENT_STATE]=4;}}
    else if(st==4){e->raw[0x20]=entity101_choose_mode(e);entity101_boundary_correct(e);entity101_load_motion(e);e->raw[ENT_STATE]=6;}
    else if(st==6){if(e->raw[ENT_MOTION_PHASE]==0){if(e->raw[0x2E]!=0){--e->raw[0x2E];e->raw[ENT_STATE]=4;}else if((gaw_platform_entropy8()&0xFFu)<8u){gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[0x2F]=(uint8_t)((gaw_platform_entropy8()&0x3Fu)+0x40u);e->raw[ENT_STATE]=8;}else e->raw[ENT_STATE]=4;}}
    else if(st==8){if(--e->raw[0x2F]==0){e->raw[0x2E]=0x14;e->raw[ENT_STATE]=4;}}
    entity101_update_orbit(e);return 1;
}


/* Types $6A/$6B/$7C (106,107,124), wrapper $54D3 + bank-2 table $AB40. */
static int entity106_family_handler(GawEntity *e) {
    switch(e->raw[ENT_STATE]){
        case 0:e->raw[0x13]=0x80;e->raw[0x11]=0x38;e->raw[ENT_HIT_FLASH_TIMER]=0x20;e->raw[ENT_MOTION_PHASE]=0x38;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x5A;e->raw[0x09]=0x9D;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=7;e->raw[ENT_STATE]=2;break;
        case 2:if(e->raw[ENT_ANIM_FRAME]==6u){e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAME]=6;e->raw[ENT_STATE]=4;}break;
        case 4:e->raw[ENT_STATE]=6;break;
        case 6:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=2;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x08]=0xDA;e->raw[0x09]=0x9D;e->raw[ENT_MOTION_PHASE]=0x34;e->raw[ENT_STATE]=8;}break;
        case 8:if(e->raw[ENT_MOTION_PHASE]==0){for(int b=8;b>0;--b){GawEntity*c=entity_spawn_aux_ptr(e,0x74u);if(!c)break;c->raw[ENT_DIRECTION]=(uint8_t)(b-1);}e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=0x0A;}break;
        case 0x0A:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x20]=0;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xC4;e->raw[0x09]=0x9D;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=7;e->raw[ENT_STATE]=0x0C;}break;
        case 0x0C:if(e->raw[ENT_ANIM_FRAME]==6u){e->raw[ENT_FLAGS]&=(uint8_t)~3u;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_STATE]=0x0E;}break;
        case 0x0E:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x5A;e->raw[0x09]=0x9D;if(entity32_try_spawn(e))e->raw[ENT_STATE]=2;}break;
        default:break;
    }
    return 1;
}


/* $577F/$5467, shared by the 108/109 boss phases. */
static int entity108_direction_to_offset(GawEntity *e,uint8_t yoff,uint8_t xoff,uint8_t *out) {
    static const uint8_t map[16]={0,0,2,3,0,0,2,3,0,0,4,5,1,1,6,7};
    uint8_t d=0,target=(uint8_t)(gaw_ram_read8(PLAYER_Y_ADDR)+yoff),v=e->raw[0x13];
    if(target!=v){d|=2u;if(target>=v)d|=1u;}
    target=(uint8_t)(gaw_ram_read8(PLAYER_X_ADDR)+xoff);v=e->raw[0x11];
    if(target!=v){d|=8u;if(target>=v)d|=4u;}
    if(d&2u){v=e->raw[0x13];if((d&1u)?(v>=0xD0u):(v<0x31u))d&=(uint8_t)~2u;}
    if(d&8u){v=e->raw[0x11];if((d&4u)?(v>=0x88u):(v<0x31u))d&=(uint8_t)~8u;}
    if((d&0x0Au)==0)return 0;
    *out=map[d&0x0Fu];
    return 1;
}
static void entity108_load_vector(GawEntity *e,uint8_t dir) {
    static const uint8_t rec[33]={0x20,0xC0,0xFF,0x00,0x00, 0x40,0x00,0x00,0x00, 0x00,0x00,0xC0,0xFF, 0x00,0x00,0x40,0x00, 0xC0,0xFF,0xC0,0xFF, 0xC0,0xFF,0x40,0x00, 0x40,0x00,0xC0,0xFF, 0x40,0x00,0x40,0x00};
    const uint8_t*q=rec+1u+(unsigned)(dir&7u)*4u;e->raw[ENT_MOTION_PHASE]=rec[0];e->raw[ENT_DELTA0]=q[0];e->raw[ENT_DELTA0+1]=q[1];e->raw[ENT_DELTA1]=q[2];e->raw[ENT_DELTA1+1]=q[3];
}
static void entity108_phase2_init(GawEntity *e) {e->raw[ENT_MOTION_PHASE]=0x40;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;}
static void entity108_spawn117(GawEntity *e) {(void)entity_spawn_aux(e,0x75u);}
static void entity108_spawn118_four(GawEntity *e) {uint8_t d=(uint8_t)(gaw_platform_entropy8()&3u);for(int b=4;b>0;--b){GawEntity*c=entity_spawn_aux_ptr(e,0x76u);if(!c)break;c->raw[0x21]=(uint8_t)(b-1);c->raw[0x20]=d;}}
static int entity108_handler(GawEntity *e) {
    switch(e->raw[ENT_STATE]){
        case 0:e->raw[0x13]=0x80;e->raw[0x11]=0x48;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_FLAGS]|=2u;e->raw[ENT_DIRECTION]=1;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_DELAY]=0x10;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_STATE]=2;break;
        case 2:if(e->raw[ENT_MOTION_PHASE]==0)e->raw[ENT_STATE]=4;break;
        case 4:{uint8_t d;if(entity108_direction_to_offset(e,0,0,&d)){e->raw[0x22]=d;entity108_load_vector(e,d);e->raw[ENT_STATE]=8;}else e->raw[ENT_STATE]=4;break;}
        case 6:entity108_load_vector(e,e->raw[0x22]);e->raw[ENT_STATE]=8;break;
        case 8:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_STATE]=4;if((gaw_platform_entropy8()&0x0Fu)<4u){e->raw[ENT_STATE]=0x0A;e->raw[0x23]=0;gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[0x08]=0xE3;e->raw[0x09]=0x9E;e->raw[ENT_MOTION_PHASE]=0x20;}}break;
        case 0x0A:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xED;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=3;e->raw[ENT_MOTION_PHASE]=0x16;e->raw[ENT_STATE]=0x0C;}break;
        case 0x0C:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_STATE]=0x0A;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[0x08]=0xE3;e->raw[0x09]=0x9E;entity108_spawn117(e);e->raw[ENT_MOTION_PHASE]=0x20;if(++e->raw[0x23]==2u)entity108_phase2_init(e);}break;
        case 0x0E: /* transition into the second phase, shared with type 109 */
            e->raw[0x13]=0x80;e->raw[0x11]=0x48;e->raw[ENT_DIRECTION]=1;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_STATE]=2;break;
        case 0x10:if(e->raw[ENT_ANIM_FRAME]==2u){entity108_spawn118_four(e);e->raw[0x08]=0x14;e->raw[0x09]=0xA0;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_MOTION_PHASE]=0x70;e->raw[ENT_STATE]=0x12;}break;
        case 0x12:if(e->raw[ENT_MOTION_PHASE]==0){unsigned alive=0;for(unsigned i=24;i<32u;++i)if(gaw_entity(i)->raw[ENT_TYPE])++alive;if(!alive)e->raw[ENT_STATE]=4;}break;
        default:break;
    }
    return 1;
}
static void entity109_try_move(GawEntity *e) {
    uint8_t d;if(entity108_direction_to_offset(e,0,0xF0u,&d)){e->raw[0x22]=d;entity108_load_vector(e,d);e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=4;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_STATE]=8;}
}
static int entity109_handler(GawEntity *e) {
    switch(e->raw[ENT_STATE]){
        case 0:e->raw[0x13]=0x80;e->raw[0x11]=0x48;e->raw[ENT_DIRECTION]=1;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_STATE]=2;break;
        case 2:if(e->raw[ENT_HIT_FLASH_TIMER]==0){e->raw[ENT_FLAGS]|=2u;e->raw[ENT_STATE]=4;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_TICK]=0;e->raw[ENT_STATE]=6;entity109_try_move(e);}break;
        case 4:e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_TICK]=0;e->raw[ENT_STATE]=6;entity109_try_move(e);break;
        case 6:entity109_try_move(e);break;
        case 8:if(e->raw[ENT_MOTION_PHASE]==0){gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);if(r<4u){e->raw[0x08]=0xA9;e->raw[0x09]=0x9F;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_TICK]=0;e->raw[ENT_ANIM_DELAY]=0x0C;e->raw[ENT_ANIM_FRAMES]=3;e->raw[ENT_STATE]=0x10;}else if(r<0x0Cu && (uint8_t)(gaw_ram_read8(PLAYER_X_ADDR)-0x10u)>=e->raw[0x11]){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[0x08]=0xE3;e->raw[0x09]=0x9E;e->raw[0x23]=3;e->raw[ENT_MOTION_PHASE]=0x20;e->raw[ENT_STATE]=0x0A;}else e->raw[ENT_STATE]=6;}break;
        case 0x0A:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0xED;e->raw[0x09]=0x9E;e->raw[ENT_ANIM_DELAY]=8;e->raw[ENT_ANIM_FRAMES]=3;e->raw[ENT_MOTION_PHASE]=0x12;e->raw[ENT_STATE]=0x0C;}break;
        case 0x0C:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[0x08]=0xE3;e->raw[0x09]=0x9E;entity108_spawn117(e);e->raw[ENT_MOTION_PHASE]=0x14;e->raw[ENT_STATE]=0x0A;if(--e->raw[0x23]==0)e->raw[ENT_STATE]=0x12;}break;
        case 0x0E:e->raw[0x13]=0x80;e->raw[0x11]=0x48;e->raw[ENT_DIRECTION]=1;e->raw[0x08]=0x28;e->raw[0x09]=0x9E;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_STATE]=2;break;
        case 0x10:if(e->raw[ENT_ANIM_FRAME]==2u){entity108_spawn118_four(e);e->raw[0x08]=0x14;e->raw[0x09]=0xA0;e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_MOTION_PHASE]=0x70;e->raw[ENT_STATE]=0x12;}break;
        case 0x12:if(e->raw[ENT_MOTION_PHASE]==0){unsigned alive=0;for(unsigned i=24;i<32u;++i)if(gaw_entity(i)->raw[ENT_TYPE])++alive;if(!alive)e->raw[ENT_STATE]=4;}break;
        default:break;
    }
    if(gaw_ram_read8(0xC0DFu)!=1u || gaw_ram_read8(0xC0E1u)!=2u)e->raw[ENT_PENDING_DAMAGE]=0;
    return 1;
}


/* Types $67-$69/$7A-$7B (103..105,122..123), shared direct handler
   $51AE.  105/123 only differ in the alternate-attack probability. */
static const uint8_t entity103_move[33]={0x10,0x80,0xFF,0x00,0x00, 0x80,0x00,0x00,0x00, 0x00,0x00,0x80,0xFF, 0x00,0x00,0x80,0x00, 0x80,0xFF,0x80,0xFF, 0x80,0xFF,0x80,0x00, 0x80,0x00,0x80,0xFF, 0x80,0x00,0x80,0x00};
static const uint8_t entity103_attack_vec[32]={0xAB,0x00,0x63,0xFE, 0x9D,0x01,0x55,0xFF, 0xAB,0x00,0x9D,0x01, 0x9D,0x01,0xAB,0x00, 0x55,0xFF,0x63,0xFE, 0x63,0xFE,0x55,0xFF, 0x55,0xFF,0x9D,0x01, 0x63,0xFE,0xAB,0x00};
static const uint8_t entity103_dirs[8]={0,3,1,3,0,2,1,2};
static void entity103_reset_cycle(GawEntity *e) {e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x6A;e->raw[0x09]=0x9B;e->raw[ENT_ANIM_DELAY]=0x14;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_DIRECTION]=1;e->raw[0x25]=0x0D;e->raw[ENT_STATE]=2;}
static void entity103_load_move(GawEntity *e,uint8_t d) {const uint8_t*q=entity103_move+1u+(unsigned)(d&7u)*4u;e->raw[ENT_MOTION_PHASE]=entity103_move[0];e->raw[ENT_DELTA0]=q[0];e->raw[ENT_DELTA0+1]=q[1];e->raw[ENT_DELTA1]=q[2];e->raw[ENT_DELTA1+1]=q[3];}
static void entity103_choose_attack_vector(GawEntity *e) {
    if((gaw_platform_entropy8()&0x0Fu)>=8u){uint8_t d=(uint8_t)(e->raw[0x20]&7u);const uint8_t*q=entity103_attack_vec+(unsigned)d*4u;e->raw[ENT_DELTA1]=q[0];e->raw[ENT_DELTA1+1]=q[1];e->raw[ENT_DELTA0]=q[2];e->raw[ENT_DELTA0+1]=q[3];e->raw[ENT_DIRECTION]=entity103_dirs[d];}
    else entity_load_octant_vector(e,entity103_attack_vec);
    e->raw[0x21]=0x80;e->raw[ENT_STATE]=0x12;e->raw[ENT_MOTION_PHASE]=0x20;
}
static void entity103_start_primary_attack(GawEntity *e) {gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0xD6;e->raw[0x09]=0x9B;e->raw[ENT_ANIM_DELAY]=4;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=8;e->raw[ENT_STATE]=0x0A;}
static void entity103_start_alt_attack(GawEntity *e) {gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[0x08]=0xAE;e->raw[0x09]=0x9C;e->raw[ENT_MOTION_PHASE]=0x1A;e->raw[ENT_STATE]=0x0E;}
static int entity103_family_handler(GawEntity *e,uint8_t type) {
    switch(e->raw[ENT_STATE]){
        case 0:e->raw[ENT_FLAGS]|=3u;e->raw[0x13]=0x80;e->raw[0x11]=0x38;e->raw[ENT_DIRECTION]=1;e->raw[ENT_HIT_FLASH_TIMER]=0x40;e->raw[ENT_MOTION_PHASE]=0x40;e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x6A;e->raw[0x09]=0x9B;e->raw[ENT_ANIM_DELAY]=0x14;e->raw[ENT_ANIM_FRAMES]=2;e->raw[0x25]=0x0D;e->raw[ENT_STATE]=2;break;
        case 2:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_STATE]=4;uint8_t d;if(entity108_direction_to_offset(e,0,0,&d)){e->raw[0x22]=d;entity103_load_move(e,d);e->raw[ENT_STATE]=8;}}break;
        case 4:{uint8_t d;if(entity108_direction_to_offset(e,0,0,&d)){e->raw[0x22]=d;entity103_load_move(e,d);e->raw[ENT_STATE]=8;}break;}
        case 6:entity103_load_move(e,e->raw[0x22]);e->raw[ENT_STATE]=8;break;
        case 8:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_STATE]=4;uint8_t r=gaw_platform_entropy8();if(r<0x20u){if((type==105u||type==123u) && (r&0x0Fu)<6u)entity103_start_alt_attack(e);else entity103_start_primary_attack(e);}}break;
        case 0x0A:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[ENT_ANIM_FRAME]=0;e->raw[0x08]=0x39;e->raw[0x09]=0x9C;e->raw[ENT_ANIM_DELAY]=2;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_MOTION_PHASE]=0x18;e->raw[ENT_STATE]=0x0C;}break;
        case 0x0C:if(e->raw[ENT_MOTION_PHASE]==0)entity103_reset_cycle(e);break;
        case 0x0E:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x08]=0xE8;e->raw[0x09]=0x9C;e->raw[ENT_ANIM_DELAY]=1;e->raw[ENT_ANIM_FRAMES]=2;e->raw[ENT_STATE]=0x10;}break;
        case 0x10:e->raw[0x20]=(uint8_t)(gaw_platform_entropy8()&7u);entity103_choose_attack_vector(e);break;
        case 0x12:{uint8_t edge=0xFFu;if(e->raw[0x11]<0x38u)edge=0;else if(e->raw[0x11]>=0x90u)edge=1;else if(e->raw[0x13]<0x30u)edge=2;else if(e->raw[0x13]>=0xD0u)edge=3;else{if(e->raw[ENT_MOTION_PHASE]!=0)break;if(--e->raw[0x21]!=0){e->raw[ENT_MOTION_PHASE]=0x20;break;}edge=e->raw[ENT_DIRECTION]&3u;}
            if(--e->raw[0x25]==0){e->raw[0x11]&=0xF8u;e->raw[0x13]&=0xF8u;e->raw[ENT_ACCUM0]=0;e->raw[ENT_ACCUM1]=0;gaw_entity_set16(e,ENT_DELTA0,0);gaw_entity_set16(e,ENT_DELTA1,0);e->raw[ENT_MOTION_PHASE]=0;e->raw[ENT_ANIM_FRAME]=0;entity103_reset_cycle(e);break;}
            static const uint8_t choices[16]={3,6,2,7, 4,0,5,1, 0,3,1,2, 5,4,7,6};uint8_t r=(uint8_t)(gaw_platform_entropy8()&0x0Fu);e->raw[0x20]=choices[(unsigned)(edge&3u)*4u+(r>>2)];entity103_choose_attack_vector(e);break;}
        default:break;
    }
    return 1;
}


/* Auxiliary boss/projectile types 112..115. */
static int entity112_115_handler(GawEntity *e,uint8_t type) {
    static const uint8_t c112[22]={0x7F,0x98,0x0C,0xF8,0,0, 0x00,0xFE,0,0, 0,2,0,0, 0,0,0,0xFE, 0,0,0,2};
    static const uint8_t c113[22]={0xB3,0x98,0x10,0xF8,2,6, 0x00,0xFE,0,0, 0,2,0,0, 0,0,0,0xFE, 0,0,0,2};
    static const uint8_t c114[38]={0xAA,0x8F,0x10,0x01,2,2, 0xF4,0x00,0xB2,0xFD, 0x4E,0x02,0x0C,0xFF, 0xF4,0x00,0x4E,0x02, 0x4E,0x02,0xF4,0x00, 0x0C,0xFF,0xB2,0xFD, 0xB2,0xFD,0x0C,0xFF, 0x0C,0xFF,0x4E,0x02, 0xB2,0xFD,0xF4,0x00};
    static const uint8_t c115[22]={0x92,0x8F,0x0E,0x01,2,2, 0x80,0x02,0,0, 0x43,0x02,0x0E,0x01, 0x9A,0x01,0xEA,0x01, 0x43,0x02,0xF2,0xFE};
    if(e->raw[ENT_STATE]!=0){entity_cull_common(e);return 1;}
    if(type==114u){enemy_init_toward_player(e,c114);uint8_t cell=gaw_ram_read8(0xC046u);if(cell==0x19u){--e->raw[ENT_DELTA1+1];e->raw[ENT_DELTA0]=(uint8_t)(e->raw[ENT_DELTA0]-0x40u);}else if(cell==0x1Au){++e->raw[ENT_DELTA1+1];e->raw[ENT_DELTA0]=(uint8_t)(e->raw[ENT_DELTA0]-0x40u);}return 1;}
    const uint8_t *cfg=type==112u?c112:(type==113u?c113:c115);(void)enemy_init_standard(e,type,cfg);if(type==115u)e->raw[ENT_DIRECTION]=1;return 1;
}


/* Type $74 / 116, child emitted by the 106/107/124 boss family. */
static int entity116_handler(GawEntity *e) {
    static const uint8_t cfg[22]={0x1E,0xA0,0x18,0xE8,2,2, 0x00,0xFD,0,0, 0,3,0,0, 0,0,0,0xFD, 0,0,0,3};
    switch(e->raw[ENT_STATE]){
        case 0:(void)enemy_init_standard(e,116,cfg);e->raw[ENT_MOTION_PHASE]=0x0C;e->raw[ENT_STATE]=2;break;
        case 2:if(e->raw[ENT_MOTION_PHASE]==0){e->raw[0x22]=0x18;e->raw[ENT_STATE]=4;}break;
        case 4:if(--e->raw[0x22]==0){if(gaw_entity(16)->raw[ENT_TYPE]==106u){e->raw[0x22]=0x20;e->raw[ENT_STATE]=8;}else{e->raw[0x08]=0x48;e->raw[0x09]=0xA0;e->raw[ENT_ANIM_DELAY]=0;e->raw[ENT_ANIM_FRAMES]=0;e->raw[ENT_MOTION_PHASE]=0x60;e->raw[ENT_STATE]=6;}}break;
        case 6:entity_cull_common(e);break;
        case 8:if(--e->raw[0x22]==0){e->raw[ENT_HIT_FLASH_TIMER]=0x38;e->raw[0x22]=0x38;e->raw[ENT_STATE]=0x0A;}break;
        case 0x0A:if(--e->raw[0x22]==0)gaw_entity_clear(e);break;
        default:break;
    }
    return 1;
}


/* Type $75 / 117, bouncing/homing boss projectile. */
static int16_t entity117_adjust_toward(int16_t vel,uint8_t pos,uint8_t target,int step) {int16_t v=(int16_t)(vel+(pos>=target?-step:step));int8_t hi=(int8_t)((uint16_t)v>>8);int a=hi<0?-hi:hi;return a<3?v:vel;}
static void entity117_wrapper(GawEntity *e) {
    e->raw[ENT_MOTION_PHASE]=8;uint8_t c=e->raw[0x21];int16_t vx=(int16_t)gaw_entity_get16(e,ENT_DELTA0),vy=(int16_t)gaw_entity_get16(e,ENT_DELTA1);
    if(e->raw[0x11]<0x20u && vx<0){vx=(int16_t)-vx;c=1;}if(e->raw[0x11]>=0x90u && vx>=0){vx=(int16_t)-vx;c=1;}gaw_entity_set16(e,ENT_DELTA0,(uint16_t)vx);
    if(e->raw[0x13]<0x28u && vy<0){vy=(int16_t)-vy;c=1;}if(e->raw[0x13]>=0xD8u && vy>=0){vy=(int16_t)-vy;c=1;}gaw_entity_set16(e,ENT_DELTA1,(uint16_t)vy);
    if(e->raw[ENT_FLAGS]&4u)c=1;
    if(e->raw[0x22]<0x30u)c=1;
    e->raw[0x21]=c;
    if(--e->raw[0x22]==0)gaw_entity_clear(e);
}
static int entity117_handler(GawEntity *e) {
    static const uint8_t cfg[38]={0x58,0xA0,0x14,0x08,4,4, 0xDC,0x00,0xED,0xFD, 0x13,0x02,0x24,0xFF, 0xDC,0x00,0x13,0x02, 0x13,0x02,0xDC,0x00, 0x24,0xFF,0xED,0xFD, 0xED,0xFD,0x24,0xFF, 0x24,0xFF,0x13,0x02, 0xED,0xFD,0xDC,0x00};
    uint8_t st=e->raw[ENT_STATE];
    if(st==0){e->raw[0x21]=0;e->raw[0x22]=0xC0;enemy_init_toward_player(e,cfg);}
    else if(st==2){if(e->raw[0x21])e->raw[ENT_STATE]=4;else{int16_t vx=(int16_t)gaw_entity_get16(e,ENT_DELTA0),vy=(int16_t)gaw_entity_get16(e,ENT_DELTA1);vx=entity117_adjust_toward(vx,e->raw[0x11],gaw_ram_read8(PLAYER_X_ADDR),0x20);vy=entity117_adjust_toward(vy,e->raw[0x13],gaw_ram_read8(PLAYER_Y_ADDR),0x20);gaw_entity_set16(e,ENT_DELTA0,(uint16_t)vx);gaw_entity_set16(e,ENT_DELTA1,(uint16_t)vy);}}
    else if(st==4){GawEntity*p=gaw_entity(16);int16_t vx=(int16_t)gaw_entity_get16(e,ENT_DELTA0),vy=(int16_t)gaw_entity_get16(e,ENT_DELTA1);vx=entity117_adjust_toward(vx,e->raw[0x11],p->raw[0x11],0x30);vy=entity117_adjust_toward(vy,e->raw[0x13],p->raw[0x13],0x30);unsigned hit=0;int16_t nv=vx;uint8_t dx=(uint8_t)(e->raw[0x11]-p->raw[0x11]);if(vx>=0){if(e->raw[0x11]<p->raw[0x11]&&dx>=0xE8u){nv=(int16_t)(vx-0x18);hit|=1u;}}else if(e->raw[0x11]>=p->raw[0x11]&&dx<0x18u){nv=(int16_t)(vx+0x18);hit|=1u;}vx=nv;uint8_t dy=(uint8_t)(e->raw[0x13]-p->raw[0x13]);nv=vy;if(vy>=0){if(e->raw[0x13]<p->raw[0x13]&&dy>=0xF0u){nv=(int16_t)(vy-0x18);hit|=2u;}}else if(e->raw[0x13]>=p->raw[0x13]&&dy<0x10u){nv=(int16_t)(vy+0x18);hit|=2u;}vy=nv;gaw_entity_set16(e,ENT_DELTA0,(uint16_t)vx);gaw_entity_set16(e,ENT_DELTA1,(uint16_t)vy);if(hit==3u)gaw_entity_clear(e);}
    entity117_wrapper(e);
    return 1;
}


/* Type $76 / 118, path-table child emitted four-at-a-time by the 108/109
   boss.  The nested pointer graph at $4745-$47F6 is retained byte-for-byte. */
static const uint8_t entity118_path_data[0xB2]={
#include "entity118_path_data.inc"
};
static uint8_t entity118_d8(uint16_t a){return (a>=0x4745u&&a<=0x47F6u)?entity118_path_data[a-0x4745u]:0xFFu;}
static uint16_t entity118_d16(uint16_t a){return (uint16_t)(entity118_d8(a)|((uint16_t)entity118_d8((uint16_t)(a+1u))<<8));}
static int entity118_handler(GawEntity *e) {
    if(e->raw[ENT_STATE]==0){e->raw[ENT_ATTACK]=0x1C;e->raw[ENT_FLAGS]=0x13;e->raw[0x08]=0xA4;e->raw[0x09]=0xA0;e->raw[ENT_ANIM_DELAY]=6;e->raw[ENT_ANIM_FRAMES]=4;e->raw[0x22]=0;e->raw[ENT_STATE]=2;}
    if(e->raw[ENT_STATE]==2){e->raw[ENT_ANIM_FRAME]=0;e->raw[ENT_ANIM_TICK]=0;uint16_t p=entity118_d16((uint16_t)(0x4745u+(unsigned)e->raw[0x20]*8u+(unsigned)e->raw[0x21]*2u));uint16_t q=(uint16_t)(p+(unsigned)e->raw[0x22]*2u);uint8_t yo=entity118_d8(q);if(yo==0xFFu){gaw_entity_clear(e);return 1;}uint8_t xo=entity118_d8((uint16_t)(q+1u));e->raw[0x13]=(uint8_t)(gaw_ram_read8(0xC613u)+yo);if(e->raw[0x13]<0x19u||e->raw[0x13]>=0xE8u){gaw_entity_clear(e);return 1;}e->raw[0x11]=(uint8_t)(gaw_ram_read8(0xC611u)+xo);if(e->raw[0x11]<0x19u||e->raw[0x11]>=0x91u){gaw_entity_clear(e);return 1;}e->raw[ENT_STATE]=4;}
    else if(e->raw[ENT_STATE]==4){uint8_t a=(uint8_t)(e->raw[ENT_ANIM_FRAME]+1u);if(a>=e->raw[ENT_ANIM_FRAMES]){a=(uint8_t)(e->raw[ENT_ANIM_TICK]+1u);if(a>=e->raw[ENT_ANIM_DELAY]){--e->raw[ENT_ANIM_TICK];++e->raw[0x22];e->raw[ENT_STATE]=2;}}}
    return 1;
}
/* Type $77 / 119, short straight projectile. */
static int entity119_handler(GawEntity *e) {
    static const uint8_t cfg[22]={0x15,0x97,0x01,0x00,0,0, 0x20,0xFD,0,0, 0xE0,0x02,0,0, 0,0,0x20,0xFD, 0,0,0xE0,0x02};
    if(e->raw[ENT_STATE]==0){uint8_t d=3;if(e->raw[0x13]!=0x20u)d=2;if(e->raw[0x11]<0x21u)d=1;e->raw[ENT_DIRECTION]=d;(void)enemy_init_standard(e,119,cfg);return 1;}
    if(e->raw[0x11]<0x1Cu||e->raw[0x11]>=0x84u||e->raw[0x13]<0x1Cu||e->raw[0x13]>=0xE4u||e->raw[ENT_MOTION_PHASE]==0)gaw_entity_clear(e);
    return 1;
}

int gaw_entity_native_handler(GawEntity *e, uint8_t type) {
    if (type == 1) return enemy_death_handler(e);
    if (type == 2) return gaw_player_handler(e);
    if (type == 3 || type == 4 || type == 5) return action_entity_handler(e,type);
    if (type == 6) { gaw_entity_clear(e); return 1; }
    if (type == 7) return boss_death_handler(e);
    if (type == 8 || type == 9 || type == 10 || type == 14) { pickup_handler(e,type); return 1; }
    if (type == 11 || type == 12 || type == 13) return resource_pickup_handler(e,type);
    if (type == 15) return special_pickup15_handler(e);
    if ((type >= 16 && type <= 26) || type == 30) return enemy_handler(e,type);
    if (type == 27) return entity27_handler(e);
    if (type == 28) return entity28_handler(e);
    if (type == 29) return entity29_handler(e);
    if (type == 31) return entity31_handler(e);
    if (type >= 32 && type <= 34) return entity32_handler(e);
    if (type >=35 && type<=37) return entity35_37_handler(e);
    if (type >=38 && type<=40) return entity38_40_handler(e);
    if (type>=41 && type<=42) return entity41_42_handler(e);
    if (type==43) return entity43_handler(e);
    if (type==44) return entity44_handler(e);
    if (type==45) return entity45_handler(e);
    if (type==46 || type==47) return entity46_47_handler(e);
    if (type==48) return entity48_handler(e);
    if (type==49 || type==50) return entity49_50_handler(e);
    if (type==51 || type==52) return entity51_52_handler(e);
    if (type>=53 && type<=55) return entity53_55_handler(e);
    if (type==56 || type==57) return entity56_57_handler(e);
    if (type==58 || type==59) return entity58_59_handler(e);
    if (type==60) return entity60_handler(e);
    if (type==61 || type==62 || type==64) return entity61_62_64_handler(e,type);
    if (type==63) return entity63_handler(e);
    if (type==65) return entity65_handler(e);
    if (type==66) return entity66_handler(e);
    if (type>=67 && type<=69) return entity67_69_handler(e,type);
    if (type==70) return entity70_handler(e);
    if (type>=71 && type<=73) return entity71_73_handler(e,type);
    if (type==74 || type==75) return entity74_75_handler(e,type);
    if (type==76) return entity76_handler(e);
    if (type==77 || type==78) { int r=entity77_78_handler(e,type); entity77_wrapper_resource(e); return r; }
    if (type>=79 && type<=81) return entity79_81_handler(e,type);
    if (type==82) { int r=entity82_handler(e); entity77_wrapper_resource(e); return r; }
    if (type==83) { int r=entity83_handler(e); entity83_wrapper_hud(e); return r; }
    if (type==84 || type==85) return entity84_85_handler(e,type);
    if (type==86) return entity86_handler(e);
    if (type==87 || type==88) return entity87_88_handler(e,type);
    if (type==89 || type==90) return entity89_90_handler(e,type);
    if (type==91) return entity91_handler(e);
    if (type==92 || type==93) { int r=entity92_93_handler(e,type); entity92_93_wrapper_damage(e); return r; }
    if (type==94) return entity94_handler(e);
    if (type==95 || type==96) return entity95_96_handler(e,type);
    if (type==97 || type==98) return entity97_98_handler(e,type);
    if (type==99 || type==100 || type==120 || type==121) return entity99_family_handler(e,type);
    if (type==101) return entity101_handler(e);
    if (type==102) return entity102_handler(e);
    if ((type>=103 && type<=105) || type==122 || type==123) return entity103_family_handler(e,type);
    if (type==106 || type==107 || type==124) return entity106_family_handler(e);
    if (type==108) return entity108_handler(e);
    if (type==109) return entity109_handler(e);
    if (type==110 || type==111 || type>=125) { gaw_entity_clear(e); return 1; }
    if (type>=112 && type<=115) return entity112_115_handler(e,type);
    if (type==116) return entity116_handler(e);
    if (type==117) return entity117_handler(e);
    if (type==118) return entity118_handler(e);
    if (type==119) return entity119_handler(e);
    return 0;
}
