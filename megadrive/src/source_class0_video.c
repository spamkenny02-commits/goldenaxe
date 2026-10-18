#include "source_class0_video.h"
#include "source_class0_video_assets_generated.h"
#ifdef SGDK_GCC
#include <genesis.h>
#endif

u16 source_class0_video_word(u16 sms)
{return gaw_sms_md_attributes[((sms&255)<<8)|(sms>>8)];}

void source_class0_video_map(const u8 *sms,u16 *native,u16 words)
{
#ifdef SGDK_GCC
    u16 count;
    if(!words) return;
    /* A128KiB ROM LUT accepts the raw word without byte swapping/masking.
     * Four words share a DBRA, including a bounded tail for arbitrary counts. */
    #define VIDEO_WORD "moveq #0,%%d0\n\t" \
        "move.w (%0)+,%%d0\n\t" \
        "add.l %%d0,%%d0\n\t" \
        "move.w (%3,%%d0.l),(%1)+\n\t"
    if(words>=4)
    {
        count=(words>>2)-1;
        __asm__ volatile ("1: " VIDEO_WORD VIDEO_WORD VIDEO_WORD VIDEO_WORD "dbra %2,1b"
        : "+&a" (sms),"+&a" (native),"+&d" (count)
        : "a" (gaw_sms_md_attributes) : "d0","cc","memory");
    }
    words&=3;
    if(words)
    {
        count=words-1;
        __asm__ volatile ("1: " VIDEO_WORD "dbra %2,1b"
        : "+&a" (sms),"+&a" (native),"+&d" (count)
        : "a" (gaw_sms_md_attributes) : "d0","cc","memory");
    }
    #undef VIDEO_WORD
#else
    while(words--)
    {
        u16 word=sms[0]|((u16)sms[1]<<8);sms+=2;
        *native++=source_class0_video_word(word);
    }
#endif
}

void source_class0_video_palette(const u8 *upper,u16 *native)
{
    u16 n;
    for(n=0;n<16;n++)
    {
        native[n]=gaw_sms_md_colors[gaw_class0_sms_palette[n]&63];
        native[16+n]=gaw_sms_md_colors[upper[n]&63];
    }
    native[0]=0; /* Source zero pixels reveal the supplied backdrop plane. */
}

u16 source_class0_video_background(void) {return GAW_CLASS0_BACKGROUND_COLOR;}
const u32 *source_class0_video_patterns(void) {return gaw_class0_md_patterns;}

#ifdef SGDK_GCC
u8 source_class0_video_upload(const u16 *map,const u16 *palette)
{
    u16 row,address,width;
    vu32 *control=(vu32*)VDP_CTRL_PORT;
    if(!map || !palette || VDP_isEnable()) return 0;
    /* The hidden H40 bus has more DMA slots per line. Restore the caller's
     * H32 width before return; this never changes a displayed frame. */
    width=VDP_getScreenWidth();
    if(width==256) VDP_setScreenWidth320();
    VDP_loadTileData(gaw_class0_md_patterns,16,193,DMA);
    /* Short rows cost more in generic transfer setup than in data movement.
     * BG_A64x32 gives a128-byte stride; each visible row is16 longwords. */
    VDP_setAutoInc(2);address=VDP_getPlaneAddress(BG_A,0,2);
    for(row=0;row<24;row++)
    {
        *control=VDP_WRITE_VRAM_ADDR(address);address+=128;
        __asm__ volatile (
            ".rept 16\n\tmove.l (%0)+,(%1)\n\t.endr"
            : "+&a" (map) : "a" ((vu32*)VDP_DATA_PORT) : "cc","memory");
    }
    PAL_setColors(0,palette,32,DMA);
    if(width==256) VDP_setScreenWidth256();
    return 1;
}
#endif
