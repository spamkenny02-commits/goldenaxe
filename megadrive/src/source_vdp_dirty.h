#ifndef GAW_SOURCE_VDP_DIRTY_H
#define GAW_SOURCE_VDP_DIRTY_H
#include <types.h>
/* Mode4/192 room layout: patterns0..3FFF, name table3800..3DFF,
 * SAT3F00/3F80. Conservative value changes, not physical port deadlines.
 * Producer accumulates until a successful consumer commit, then clears. */
typedef struct {u8 patterns[64],names[96];u32 palette;u8 sat;} SourceVdpDirty;
static inline void source_vdp_dirty_clear(SourceVdpDirty *d)
{u16 n;for(n=0;n<64;n++)d->patterns[n]=0;for(n=0;n<96;n++)d->names[n]=0;d->palette=0;d->sat=0;}
static inline void source_vdp_dirty_vram(SourceVdpDirty *d,u16 address)
{
 u16 tile,word;if(!d)return;address&=0x3fff;tile=address>>5;d->patterns[tile>>3]|=1<<(tile&7);
 if(address>=0x3800 && address<0x3e00){word=(address-0x3800)>>1;d->names[word>>3]|=1<<(word&7);}
 if((address>=0x3f00 && address<0x3f40) || address>=0x3f80)d->sat=1;
}
#endif
