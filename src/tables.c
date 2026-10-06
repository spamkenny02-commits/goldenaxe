#include "include/gaw_tables.h"

const uint16_t gaw_main_state_targets[12] = {
#include "main_states.inc"
};

/* $2B63-$2C62: 128 handler pointers. Type 0 is skipped by $26B6. */
const uint16_t gaw_entity_handler_targets[128] = {
#include "entity_handlers.inc"
};

const uint16_t gaw_entity_hit_targets[4] = {
#include "entity_hit.inc"
};

/* Bank 2, CPU $B762-$BB61: 512 world-cell callbacks. $BB62 begins
   the progression-event table, proving the exact table boundary. */
const uint16_t gaw_world_callback_targets[512] = {
#include "world_callbacks_512.inc"
};


/* Bank 2 CPU $8100-$81BF. Each record is: signed min Y, Y extent, signed min X, X extent. */
const uint8_t gaw_hitboxes[48][4] = {
#include "hitboxes.inc"
};

/* Configuration records consumed by original helpers $3DAF/$3ED6. */
const uint8_t gaw_enemy_configs[33][38] = {
#include "enemy_configs.inc"
};

/* ROM $3F4F: direction/facing code selected by $3F07. */
const uint8_t gaw_direction_codes[8] = {0x00,0x03,0x01,0x03,0x00,0x02,0x01,0x02};

const uint8_t gaw_enemy_config25_alt[22] = {
#include "enemy_config25_alt.inc"
};
