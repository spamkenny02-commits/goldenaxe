#ifndef GAW_ASSETS_H
#define GAW_ASSETS_H
#include <stdint.h>
/* Original four-plane RLE resource stream, returns next source address. */
uint16_t gaw_assets_unpack_tiles(uint8_t bank,uint16_t source,uint16_t destination);
/* $2AF4: item/resource dispatch into the portable VRAM shadow. */
void gaw_assets_load_item(uint8_t item,uint16_t destination);
void gaw_assets_load_map_entity(uint8_t type,uint8_t gfx_slot); /* $187D-$18CC */
void gaw_assets_remap_tiles(uint16_t source,uint16_t destination,uint8_t table_offset);
void gaw_assets_update_inventory(void);
void gaw_assets_restore_inventory(void);
uint16_t gaw_assets_unpack_ram(uint8_t bank,uint16_t source,uint16_t destination,uint8_t lanes);
void gaw_assets_restore_scene(void); /* $16EF */
#endif
