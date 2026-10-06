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
int gaw_sms_compat_indexed_call(uint8_t bank,uint16_t addr,uint16_t ix);
/* Executes the original resource decoder too, without its accelerator. */
int gaw_sms_compat_raw_call_args(uint8_t bank,uint16_t addr,uint16_t hl,uint16_t de,uint16_t bc,uint8_t a);
/* Test-only original IRQ video block: stops before audio/input at $019C. */
int gaw_sms_compat_irq_video_call(void);
int gaw_sms_compat_irq_call(void); /* isolated full $0038, no shared native tick */
#include "gaw_video.h"
#endif
