#ifndef GAW_MD_SOURCE_ROOM_FRAME_H
#define GAW_MD_SOURCE_ROOM_FRAME_H
#include <genesis.h>
#include "pattern_convert.h"
#include "source_sms_sprite8.h"
#include "source_vdp_dirty.h"
typedef struct {
 SourceSmsSprite8 sprites;
 u32 patterns[64];u16 foreground[32],background[32],palette[64];u8 sat[192];
 u16 error,ready,uploaded_patterns,uploaded_words,uploaded_clones;u8 regs[4];
} MdSourceRoomFrame;
enum {MD_SOURCE_ROOM_OK,MD_SOURCE_ROOM_INVALID};
/* Static room presentation: source name table3800, SAT3F00/3F80,8x8 sprites,
 * no zoom, scroll zero. Explicit mode/backdrop inputs, not inferred shadows.
 * Source16KiB VRAM/32-byte CRAM and state are disjoint. Display disabled,
 * H32/224, both planes64x32; caller owns VDP without IRQ/DMA reentry.
 * Streams512 converted tiles and masked sprite clones with bounded scratch.
 * Leaves display disabled. No transition deadlines or physical pacing here. */
u8 md_source_room_frame_upload(MdSourceRoomFrame *state,const u8 *vram,const u8 *cram,
 u8 reg0,u8 reg1,u8 reg6,u8 reg7,u8 reg8,u8 reg9);
/* Same room mode after successful full upload. Applies accumulated value
 * changes, including sprite clones whose source tiles/masks changed. The
 * caller owns VDP and schedules work in a safe window; this supplies no
 * beam/deadline guarantee. Leaves display state and dirty flags unchanged.
 * All mode inputs remain explicit. Buffers stay immutable until return. */
u8 md_source_room_frame_update(MdSourceRoomFrame *state,const u8 *vram,const u8 *cram,
 const SourceVdpDirty *dirty,u8 reg0,u8 reg1,u8 reg6,u8 reg7,u8 reg8,u8 reg9);
#endif
