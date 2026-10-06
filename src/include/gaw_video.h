#ifndef GAW_VIDEO_H
#define GAW_VIDEO_H
#include <stdint.h>
/* Portable SMS presentation shadow; no instruction interpreter dependency. */
void gaw_video_reset(void);
uint8_t gaw_video_status_read(void);
void gaw_video_vblank_pending(void);
void gaw_video_status_pending(uint8_t flags); /* VBlank/collision/overflow status */
void gaw_video_write_at(uint16_t address,uint8_t value);
const uint8_t *gaw_sms_vram(void);
const uint8_t *gaw_sms_cram(void);
const uint8_t *gaw_sms_vdp_regs(void);
int gaw_sms_take_tile_dirty(unsigned tile);
void gaw_sms_mark_all_tiles_dirty(void);
void gaw_sms_vdp_control_write(uint8_t value);
void gaw_sms_vdp_data_write(uint8_t value);
uint8_t gaw_sms_vdp_data_read(void);
int gaw_sms_take_name_dirty(void);
int gaw_sms_take_sat_dirty(void);
uint8_t gaw_sms_rom_bank_read(uint8_t bank,uint16_t cpu_addr);
#endif
