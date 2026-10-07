#ifndef GAW_VIDEO_H
#define GAW_VIDEO_H
#include <stdint.h>
/* Portable SMS presentation shadow; no instruction interpreter dependency. */
void gaw_video_reset(void);
uint8_t gaw_video_status_read(void);
void gaw_video_vblank_pending(void);
/* SMS Mode 4, 192-line sprite flags; pure calculation, no ROM dependency. */
uint8_t gaw_video_sprite_status(const uint8_t *vram,const uint8_t *regs);
void gaw_video_status_pending(uint8_t flags); /* VBlank/collision/overflow status */
void gaw_video_write_at(uint16_t address,uint8_t value);
const uint8_t *gaw_sms_vram(void);
const uint8_t *gaw_sms_cram(void);
const uint8_t *gaw_sms_vdp_regs(void);
int gaw_sms_take_tile_dirty(unsigned tile);
int gaw_sms_take_next_tile_dirty(void); /* ascending dirty tiles, -1 when drained */
void gaw_sms_mark_all_tiles_dirty(void);
void gaw_sms_vdp_control_write(uint8_t value);
void gaw_sms_vdp_data_write(uint8_t value);
void gaw_sms_vdp_data_write_block(const uint8_t *source,unsigned count);
uint8_t gaw_sms_vdp_data_read(void);
int gaw_sms_take_name_dirty(void);
uint32_t gaw_sms_take_name_rows_dirty(void); /* alternate consumption of 28 dirty rows */
int gaw_sms_take_sat_dirty(void);
uint8_t gaw_sms_rom_bank_read(uint8_t bank,uint16_t cpu_addr);
const uint8_t *gaw_sms_rom_bank_data(uint8_t bank,uint16_t cpu_addr);
#endif
