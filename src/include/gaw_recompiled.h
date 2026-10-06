#ifndef GAW_RECOMPILED_H
#define GAW_RECOMPILED_H
#include <stdint.h>
#include "gaw_entity.h"
/* Mechanically translated compatibility entry points for original Z80 paths
   that have not yet been lifted to named high-level C. They execute in C and
   preserve the original mapper/RAM/port semantics. */
void gaw_recompiled_call(uint8_t bank,uint16_t cpu_address);
void gaw_recompiled_entity_call(uint8_t bank,uint16_t cpu_address,GawEntity *entity);
void gaw_recompiled_world_call(uint8_t bank,uint16_t cpu_address);
#endif
