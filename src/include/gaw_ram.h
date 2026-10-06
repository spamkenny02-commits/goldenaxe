#ifndef GAW_RAM_H
#define GAW_RAM_H

#include <stddef.h>
#include <stdint.h>

#define GAW_RAM_BASE 0xC000u
#define GAW_RAM_SIZE 0x2000u

extern uint8_t gaw_ram[GAW_RAM_SIZE];

static inline uint8_t *gaw_ram_ptr(uint16_t addr) {
    return &gaw_ram[(uint16_t)(addr - GAW_RAM_BASE)];
}
static inline uint8_t gaw_ram_read8(uint16_t addr) { return *gaw_ram_ptr(addr); }
static inline void gaw_ram_write8(uint16_t addr, uint8_t v) { *gaw_ram_ptr(addr) = v; }
static inline uint16_t gaw_ram_read16le(uint16_t addr) {
    uint8_t *p = gaw_ram_ptr(addr);
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}
static inline void gaw_ram_write16le(uint16_t addr, uint16_t v) {
    uint8_t *p = gaw_ram_ptr(addr);
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

/* High-confidence RAM symbols from Phase 2/3. */
enum {
    RAM_VDP_STATUS          = 0xC01B,
    RAM_PAUSE_NMI_COUNTER   = 0xC01C,
    RAM_MAIN_STATE          = 0xC01D,
    RAM_INPUT_HELD          = 0xC020,
    RAM_INPUT_PRESSED       = 0xC021,
    RAM_PAUSE_HELD          = 0xC022,
    RAM_PAUSE_PRESSED       = 0xC023,
    RAM_VBLANK_WAIT_FLAG    = 0xC02E,
    RAM_FRAME_COUNTER       = 0xC02F,
    RAM_TIMER_C030          = 0xC030,
    RAM_ENTITY_SLOT_INDEX   = 0xC046,
    RAM_PLAYER_TILE_FLAGS   = 0xC048,
    RAM_PLAYER_ENV_MODE     = 0xC041,
    RAM_PLAYER_SPRITE_BANK  = 0xC042,
    RAM_PLAYER_SPRITE_PTR   = 0xC043,
    RAM_PLAYER_FORCED_DIR   = 0xC068,
    RAM_PLAYER_MOTION_PTR   = 0xC069,
    RAM_WORLD_EVENT_TRIGGER = 0xC06E,
    RAM_WORLD_EVENT_TARGET  = 0xC06F,
    RAM_WORLD_EVENT_PATCH   = 0xC070,
    RAM_WORLD_PROGRESS      = 0xC100,
    RAM_ACTIVE_ENTITY_COUNT = 0xC047,
    RAM_WORLD_CALLBACK      = 0xC0A4,
    RAM_WORLD_CELL_ID       = 0xC0B9,
    RAM_ENTITIES            = 0xC300
};

void gaw_ram_reset_like_z80(void);

#endif
