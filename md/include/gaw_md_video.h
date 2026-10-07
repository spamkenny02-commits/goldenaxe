#ifndef GAW_MD_VIDEO_H
#define GAW_MD_VIDEO_H
#include <stdint.h>
uint32_t gaw_md_pattern_row(uint8_t a,uint8_t b,uint8_t c,uint8_t d);
uint16_t gaw_md_color(uint8_t color);
uint16_t gaw_md_descriptor(uint16_t descriptor);
uint16_t gaw_md_zero_descriptor(uint16_t descriptor);
unsigned gaw_md_scroll_row(uint8_t scroll,unsigned row);
uint32_t gaw_md_scroll_dirty_rows(uint32_t rows,uint8_t scroll,uint8_t right_lock);
uint16_t gaw_md_sprite_y(uint8_t y);
/* height is 8/16/32; counts saturate at eight and must start at zero per SAT. */
uint32_t gaw_md_sprite_line_mask(uint8_t y,unsigned height,uint8_t counts[192]);
uint32_t gaw_md_sprite_pattern_row(const uint8_t *vram,unsigned tile,unsigned row,
                                   unsigned zoom,unsigned column);
#endif
