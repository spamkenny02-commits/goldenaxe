#ifndef GAW_SOURCE_GAME_IRQ_H
#define GAW_SOURCE_GAME_IRQ_H
#include "source_irq_timed_context.h"
#include "source_sprite_scene_timed.h"
#include "source_wait.h"
typedef struct {u8 bytes[192];u32 first_y,first_xy;} SourceGameSatPacket;
typedef u8 (*SourceGameSatSink)(void *user,const SourceGameSatPacket *packet);
typedef u8 (*SourceGameStatusRead)(void *user,const SourceClockIrq *entry,u8 *status);

typedef struct {
 SourceTimedIrqContext timed; /* core is first; wait can use its C000 prefix. */
 u8 *ram;u8 compact[336];SourceGameSatPacket sat;
 SourceGameSatSink video;void *video_context;
 SourceGameStatusRead status_read;void *status_context;
 u16 error;u8 bound,producer_active,vdp_status;
} SourceGameIrqContext;
enum {SOURCE_GAME_IRQ_INVALID=0xa00,SOURCE_GAME_IRQ_STATUS,SOURCE_GAME_IRQ_UNSAFE,SOURCE_GAME_IRQ_VIDEO};
/* Zero-init context, configure low/bank6/lines/input and timed audio sink,
 * explicit source VDP status (including VINT), optional status provider and
 * video sink, then bind. Provider runs once per IRQ, before any side effect;
 * its entry describes0137, after the original vector status read.
 * RAM is C000..DFFF, audio is its DE00..DF8F view. Outside IRQ, core.ram
 * addresses this full view; inside canonical IRQ/trace it is compact336.
 * This context is for the game sprite/wait path, not existing compact loaders.
 * A sink copies its packet before returning; next IRQ overwrites owned data.
 * Packets carry completed-OUTI dates, every16T; Y64 then X/tile128.
 * Video prefix can publish before a later audio/IRQ failure: stop session,
 * never retry a failed IRQ. Status is an explicit caller input, not MD status.
 * This sink emits SAT only. Other canonical IRQ stages retain RAM/clock work;
 * queued tiles, HUD, palette and register delivery require separate video work.
 * The composed frame is verified with tile/HUD/queue requests empty. */
u8 source_game_irq_bind(SourceGameIrqContext *context,u8 *ram);
u8 source_game_irq_interrupt(void *context,const SourceClockIrq *entry,SourceClockWork *work);
/*0938 entry after opcode fetch -> CALL0B95 -> full wait/restore/RET. Full IRQ
 * is unsafe while producer registers are live; C02E must be zero on entry.
 * Optional trace points:0938,0B95,0BB3 andFFFF(caller after fetch).
 * Same partial/fatal contract as clocked source routines. */
u8 source_game_sprite_frame(SourceClock *clock,SourceGameIrqContext *context,const u8 *bank12,
 SourceSpriteSceneOutput *scene,SourceWaitOutput *wait,SourceSpriteSceneTrace trace,void *user);
#endif
