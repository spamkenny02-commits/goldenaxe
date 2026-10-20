#ifndef GAW_SOURCE_SPRITE_SCENE_TIMED_H
#define GAW_SOURCE_SPRITE_SCENE_TIMED_H
#include "source_sprite_scene.h"
#include "source_clock.h"
typedef u8 (*SourceSpriteSceneTrace)(void *user,u16 pc,const SourceClock *clock,const u8 *ram);
/* Dedicated native translation of0938 with source instruction boundaries.
 * Clock entry is at0938 after its first opcode fetch; no caller CALL cost.
 * Interrupt callback must preserve source foreground registers and bank12,
 * and share the same RAM view. Trace is optional, at instruction start after
 * boundary acceptance/opcode fetch. Each write commits before the next step.
 * Valid data bounded to64 entries. Failure is fatal/partial, unlike the
 * atomic builder: do not retry a session after an IRQ/trace/data failure.
 * RAM/output/clock/bank are disjoint; bank is immutable. MapperFFFF writes
 * update its RAM mirror. Stack bytes are supplied by the caller, not modeled. */
u8 source_sprite_scene_timed(SourceClock *clock,u8 *ram,const u8 *bank12,
 SourceSpriteSceneOutput *output,SourceClockInterrupt interrupt,void *context,
 SourceSpriteSceneTrace trace,void *trace_context);
#endif
