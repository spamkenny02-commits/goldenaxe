#ifndef GAW_PLATFORM_H
#define GAW_PLATFORM_H

#include <stdbool.h>
#include <stdint.h>

/* Portable boundary. SMS and Mega Drive backends will implement these later. */
void gaw_platform_init(void);
void gaw_platform_wait_vblank(void);
uint8_t gaw_platform_read_pad_sms_bits(void); /* already normalized: bits 0..5, 1 = held */
/* PSG data ($7F) and handheld stereo mask ($06). MD PSG is mono. */
void gaw_platform_sound_write(uint8_t port,uint8_t value);
/* Z80 R is used as entropy by a few original entity handlers. Backends expose
   a cheap changing byte; deterministic host tests can seed it. */
uint8_t gaw_platform_entropy8(void);
/* $2AF4 is presentation-only resource upload for pickup graphics. */
void gaw_platform_entity_resource_load(uint8_t resource_id);
/* $1780 map-entity graphics load. Gameplay assigns gfx_slot; backends may
   upload/convert the corresponding original resource for presentation. */
void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot);
/* Upload the rebuilt portable name table. Scroll animation lives in the core. */
void gaw_platform_world_rebuilt(void);
/* Presentation-only boundaries lifted from the remaining player actions. */
void gaw_platform_inventory_refresh(void);
/* Direct bank-3 string address; core resolves per-cell message tables. */
void gaw_platform_world_message(uint16_t resource,uint8_t saved_cell);
uint8_t gaw_platform_sram_read(uint16_t offset);
void gaw_platform_sram_write(uint16_t offset,uint8_t value);

#endif
