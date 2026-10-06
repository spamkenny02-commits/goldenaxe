#ifndef GAW_PLATFORM_H
#define GAW_PLATFORM_H

#include <stdbool.h>
#include <stdint.h>

/* Portable boundary. SMS and Mega Drive backends will implement these later. */
void gaw_platform_init(void);
void gaw_platform_wait_vblank(void);
uint8_t gaw_platform_read_pad_sms_bits(void); /* already normalized: bits 0..5, 1 = held */
void gaw_platform_audio_command(uint8_t command);
/* Z80 R is used as entropy by a few original entity handlers. Backends expose
   a cheap changing byte; deterministic host tests can seed it. */
uint8_t gaw_platform_entropy8(void);
/* $2AF4 is presentation-only resource upload for pickup graphics. */
void gaw_platform_entity_resource_load(uint8_t resource_id);
/* $1780 map-entity graphics load. Gameplay assigns gfx_slot; backends may
   upload/convert the corresponding original resource for presentation. */
void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot);
/* Phase 8 world/render boundaries. Host tests are no-ops; SMS/MD backends may
   use these to upload the rebuilt map or animate a cell scroll. */
void gaw_platform_world_rebuilt(void);
void gaw_platform_world_scroll_begin(void);
void gaw_platform_world_scroll_end(void);
/* Presentation-only boundaries lifted from the remaining player actions. */
void gaw_platform_inventory_refresh(void);
void gaw_platform_player_special_effect(uint8_t effect_id);
void gaw_platform_show_world_map(void);
/* Direct bank-3 string address; core resolves per-cell message tables. */
void gaw_platform_world_message(uint16_t resource,uint8_t saved_cell);
void gaw_platform_player_transition_frame(void);
uint8_t gaw_platform_sram_read(uint16_t offset);
void gaw_platform_sram_write(uint16_t offset,uint8_t value);

#endif
