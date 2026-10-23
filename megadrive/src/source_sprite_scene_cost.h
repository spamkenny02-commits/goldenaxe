#ifndef GAW_SOURCE_SPRITE_SCENE_COST_H
#define GAW_SOURCE_SPRITE_SCENE_COST_H
#include "source_sprite_scene.h"
#include "source_clock.h"
/* Same annotated 0938 native semantics, summing instructions without IRQs.
 * Mutates the caller's 8KiB shadow RAM/SAT. Low ROM covers descriptors below
 * 8000, including the screen-spell particles at6EAE. No hardware delays. */
u8 source_sprite_scene_cost(u8 *ram,const u8 *bank12,const u8 *low,
 SourceClockWork *work,SourceSpriteSceneOutput *output);
/* Algebraic equivalent for runtime pacing; T states only, no refresh count. */
u8 source_sprite_scene_tstates(u8 *ram,const u8 *bank12,const u8 *low,
 u32 *tstates,SourceSpriteSceneOutput *output);
#endif
