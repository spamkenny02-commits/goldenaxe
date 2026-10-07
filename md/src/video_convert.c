#include "gaw_md_video.h"

/* Expand eight one-bit pixels into eight four-bit pixels. Four table reads
   replace the pixel-by-pixel shifts in every dirty tile upload. */
static const uint32_t plane[256] = {
#include "pattern_plane.inc"
};

uint32_t gaw_md_pattern_row(uint8_t a,uint8_t b,uint8_t c,uint8_t d) {
    return plane[a]|(plane[b]<<1)|(plane[c]<<2)|(plane[d]<<3);
}

uint16_t gaw_md_color(uint8_t color) {
    static const uint8_t levels[4]={0,2,5,7};
    unsigned r=levels[color&3u],g=levels[(color>>2)&3u],b=levels[(color>>4)&3u];
    return (uint16_t)((b<<9)|(g<<5)|(r<<1));
}

uint16_t gaw_md_descriptor(uint16_t descriptor) {
    return (uint16_t)((descriptor&0x01FFu)|((descriptor&0x0E00u)<<2)|
                      ((descriptor&0x1000u)<<3));
}

/* Palette 2/3 colour 1 is filled with SMS background palette 0/1 colour 0.
   This layer stays below sprites even if the source descriptor has priority. */
uint16_t gaw_md_zero_descriptor(uint16_t descriptor) {
    return (uint16_t)(0x4500u|((descriptor&0x0800u)<<2));
}

/* SMS's 28-row name table wraps at 224 pixels; a 32-row MD plane wraps at 256.
   Move the coarse (32-pixel) part into name rows and keep VSRAM in 0..31.
   Visible source rows then stay within physical rows 0..27. */
unsigned gaw_md_scroll_row(uint8_t scroll,unsigned row) {
    unsigned base=(scroll>>5)*4u;
    if(base==28u)base=0;
    row+=base;
    return row>=28u?row-28u:row;
}

uint32_t gaw_md_scroll_dirty_rows(uint32_t rows,uint8_t scroll,uint8_t right_lock) {
    rows&=0x0FFFFFFFu;
    unsigned base=gaw_md_scroll_row(scroll,0);
    uint32_t rotated=base?((rows>>base)|(rows<<(28u-base))):rows;
    if(right_lock)rotated|=rows;
    return rotated&0x0FFFFFFFu;
}

uint16_t gaw_md_sprite_y(uint8_t y) {
    int line=(int)y+1;
    if(y>=0xE0u)line-=256;
    return (uint16_t)(line+128);
}
