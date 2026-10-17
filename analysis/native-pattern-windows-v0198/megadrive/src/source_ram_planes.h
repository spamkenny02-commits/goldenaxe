#ifndef GAW_SOURCE_RAM_PLANES_H
#define GAW_SOURCE_RAM_PLANES_H
#include "source_irq_context.h"
/* Original0C00 RAM decoder. Valid original streams, caller-owned buffer.
 * address controls source low-byte carry timing; stride is1,2 or4. */
u8 source_ram_planes(SourceClock *clock,SourceIrqContext *context,const u8 **source,
                      u8 *destination,u16 address,u8 stride);
#endif
