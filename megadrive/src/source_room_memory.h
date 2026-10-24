#ifndef GAW_SOURCE_ROOM_MEMORY_H
#define GAW_SOURCE_ROOM_MEMORY_H
#include "source_irq_context.h"
/* Offsets from C000. Compact IRQ/audio bytes are live aliases, not snapshots.
 * full_ram owns all other bytes; caller must initialize it before execution. */
static inline u8 source_room_get(const SourceIrqContext *ctx,u16 offset)
{
 offset&=8191;
 if(offset<80) return ctx->ram[offset];
 if(offset>=0x1d00 && offset<0x1e00) return ctx->ram[80+offset-0x1d00];
 if(offset>=0x1e00 && offset<0x1f90) return ctx->audio[offset-0x1e00];
 return ctx->full_ram[offset];
}
static inline void source_room_put(SourceIrqContext *ctx,u16 offset,u8 value)
{
 offset&=8191;
 if(offset<80) ctx->ram[offset]=value;
 else if(offset>=0x1d00 && offset<0x1e00) ctx->ram[80+offset-0x1d00]=value;
 else if(offset>=0x1e00 && offset<0x1f90) ctx->audio[offset-0x1e00]=value;
 else ctx->full_ram[offset]=value;
}
#endif
