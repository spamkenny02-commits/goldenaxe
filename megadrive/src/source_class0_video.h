#ifndef GAW_SOURCE_CLASS0_VIDEO_H
#define GAW_SOURCE_CLASS0_VIDEO_H
#include <types.h>
/* Native tile base16, source palette/priority/flips preserved.
 * The68000 map input must be even-aligned; output is naturally u16-aligned. */
u16 source_class0_video_word(u16 sms);
void source_class0_video_map(const u8 *sms,u16 *native,u16 words);
/* Upper palette is the16 bytes prepared at source DCB0..DCBF. */
void source_class0_video_palette(const u8 *upper,u16 *native);
u16 source_class0_video_background(void);
const u32 *source_class0_video_patterns(void);
#ifdef SGDK_GCC
/* Display disabled, BG_A64x32. Publishes193 tiles,768 map words and32 colors.
 * Other tile slots and the backdrop plane remain the caller's responsibility. */
u8 source_class0_video_upload(const u16 *map,const u16 *palette);
#endif
#endif
