#include "source_class0_video.h"
#include "source_class0_video_assets_generated.h"
#ifdef SGDK_GCC
#include <genesis.h>
#endif

u16 source_class0_video_word(u16 sms)
{return gaw_sms_md_attributes[sms&8191];}

void source_class0_video_map(const u8 *sms,u16 *native,u16 words)
{
    while(words--)
    {
        u16 word=sms[0]|((u16)sms[1]<<8);sms+=2;
        *native++=gaw_sms_md_attributes[word&8191];
    }
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
    if(!map || !palette || VDP_isEnable()) return 0;
    VDP_loadTileData(gaw_class0_md_patterns,16,193,DMA);
    VDP_setTileMapDataRect(BG_A,map,0,2,32,24,32,DMA);
    PAL_setColors(0,palette,32,DMA);
    return 1;
}
#endif
