#ifndef GAW_ASSETS_H
#define GAW_ASSETS_H
#include <stdint.h>
/* Original four-plane RLE resource stream, returns next source address. */
uint16_t gaw_assets_unpack_tiles(uint8_t bank,uint16_t source,uint16_t destination);
/* $2AF4: item/resource dispatch into the portable VRAM shadow. */
void gaw_assets_load_item(uint8_t item,uint16_t destination);
#endif
