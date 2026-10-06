#ifndef GAW_WORLD_H
#define GAW_WORLD_H

#include <stdbool.h>
#include <stdint.h>

/* $175F + $190B logical world-cell loader. The original compressed map
   format is executed from ROM-derived banks 8..11 and expands 160 bytes at
   $DC00 before persistent patches are restored. */
bool gaw_world_load_current_cell(void);

/* $2279/$22E2: expand the 16x10 metatile-id grid at $DC00 into the 32x20
   descriptor grid at $D600 using the 8-byte records at $C900. */
void gaw_world_expand_metatiles(void);

/* $5E90: restore progression then rebuild the CPU-side descriptor map. VDP
   presentation/HUD refresh are platform boundaries. */
void gaw_world_finalize_transition(void);

/* $5BB4-$5C93: special interior edge/gate transitions run before the per-cell
   callback. Returns true when it performed a transition/finalization. */
bool gaw_world_pre_callback_transition(void);

/* $2051 logical boundary crossing. Rendering/scroll animation is deliberately
   omitted; world id, persistence, map reload and state transition are native. */
bool gaw_world_check_boundary_transition(void);
void gaw_world_teleport(uint16_t target_cell);

/* $2260 logical reload after a neighboring-cell change. */
void gaw_world_reload_after_scroll(void);

#endif
