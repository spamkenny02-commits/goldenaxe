#ifndef GAW_SOURCE_SPRITE_SCENE_H
#define GAW_SOURCE_SPRITE_SCENE_H
#include <types.h>
typedef struct {
    u16 count,y_end,xy_end;
    u8 rotating,bank;
} SourceSpriteSceneOutput;
/* Native0938..0A71/09EE, bounded to64 entries. ram is C000..DFFF,
 * bank12 is the complete immutable16KiB source descriptor/order bank.
 * Buffers/output are disjoint. Invalid descriptor/address/capacity leaves
 * RAM/output unchanged. Successful RAM effects include pointers, hero bit,
 * collision indices, D100 sort workspace and DD40..DDFF SAT, preserving tails.
 * Caller selects mapper12 after success. No interrupt/clock/VDP effects are
 * manufactured: this atomic builder still needs source-boundary scheduling. */
u8 source_sprite_scene(u8 *ram,const u8 *bank12,SourceSpriteSceneOutput *output);
#endif
