#ifndef GAW_SOURCE_AUDIO_MEMORY_H
#define GAW_SOURCE_AUDIO_MEMORY_H
#include <types.h>
/* Captured source ROM and audio RAM. SMS RAM mirrors every8KiB; other
 * RAM regions are deliberately rejected until their source state is supplied. */
u8 source_audio_read(const u8 *state,const u8 *low,u16 low_bytes,const u8 *bank6,
                     u16 address,u8 *value);
#endif
