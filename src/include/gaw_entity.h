#ifndef GAW_ENTITY_H
#define GAW_ENTITY_H

#include <stdint.h>

#define GAW_ENTITY_COUNT 32u
#define GAW_ENTITY_SIZE  0x30u

typedef struct { uint8_t raw[GAW_ENTITY_SIZE]; } GawEntity;

/* Offsets proven by $26B6/$2768. Names marked UNKNOWN remain deliberately neutral. */
enum {
    ENT_TYPE            = 0x00,
    ENT_STATE           = 0x01,
    ENT_GFX_ID          = 0x02,
    ENT_FLAGS           = 0x03,
    ENT_MOTION_PHASE    = 0x04, /* signed countdown/phase; semantics not final */
    ENT_HIT_FLASH_TIMER = 0x05,
    ENT_COOLDOWN        = 0x06,
    ENT_SAVED_TYPE      = 0x07,
    ENT_DIRECTION       = 0x0A,
    ENT_ANIM_FRAME      = 0x0B,
    ENT_ANIM_FRAMES     = 0x0C,
    ENT_ANIM_DELAY      = 0x0D,
    ENT_ANIM_TICK       = 0x0E,
    ENT_ACCUM0          = 0x10, /* LE16 */
    ENT_ACCUM1          = 0x12, /* LE16 */
    ENT_DELTA0          = 0x14, /* LE16 */
    ENT_DELTA1          = 0x16, /* LE16 */
    ENT_HP              = 0x18, /* high confidence health-like quantity */
    ENT_ATTACK          = 0x19,
    ENT_DEFENSE         = 0x1A,
    ENT_HITBOX_SOURCE   = 0x1B,
    ENT_HITBOX_TARGET   = 0x1C,
    ENT_PENDING_DAMAGE  = 0x1D,
    ENT_RELATED_PTR     = 0x1E  /* LE16 RAM pointer */
};

GawEntity *gaw_entity(unsigned index);
uint16_t gaw_entity_addr(const GawEntity *e);
uint16_t gaw_entity_get16(const GawEntity *e, unsigned off);
void gaw_entity_set16(GawEntity *e, unsigned off, uint16_t value);
void gaw_entities_update_all(void);
void gaw_entity_apply_pending_damage(GawEntity *e);
void gaw_entity_collision_scan(GawEntity *e);
void gaw_entity_clear(GawEntity *e);
int gaw_entity_native_handler(GawEntity *e, uint8_t type);

#endif
