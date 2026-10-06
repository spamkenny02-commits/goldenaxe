#ifndef GAW_SMS_COMPAT_H
#define GAW_SMS_COMPAT_H
#include <stdint.h>
#include "gaw_entity.h"
void gaw_sms_compat_reset(void);
int gaw_sms_compat_call(uint8_t bank,uint16_t addr);
/* Differential-test entry with explicit original routine arguments. */
int gaw_sms_compat_call_args(uint8_t bank,uint16_t addr,uint16_t hl,
                             uint16_t de,uint16_t bc,uint8_t a);
int gaw_sms_compat_entity_call(uint8_t bank,uint16_t addr,GawEntity *e);
int gaw_sms_compat_world_call(uint8_t bank,uint16_t addr);
uint32_t gaw_sms_compat_faults(void);
uint16_t gaw_sms_compat_last_pc(void);
unsigned gaw_sms_compat_refresh_trace(uint8_t *values,unsigned capacity);
const uint8_t *gaw_sms_vram(void);
const uint8_t *gaw_sms_cram(void);
const uint8_t *gaw_sms_vdp_regs(void);
int gaw_sms_take_tile_dirty(unsigned tile);
void gaw_sms_mark_all_tiles_dirty(void);
/* Shared VDP model access without executing Z80 instructions. */
void gaw_sms_vdp_control_write(uint8_t value);
void gaw_sms_vdp_data_write(uint8_t value);
uint8_t gaw_sms_vdp_data_read(void);
int gaw_sms_take_name_dirty(void);
int gaw_sms_take_sat_dirty(void);
uint8_t gaw_sms_rom_bank_read(uint8_t bank,uint16_t cpu_addr);
#endif
