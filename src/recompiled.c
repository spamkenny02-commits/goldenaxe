#include "include/gaw_recompiled.h"
#include "include/gaw_sms_compat.h"
void gaw_recompiled_call(uint8_t bank,uint16_t cpu_address){(void)gaw_sms_compat_call(bank,cpu_address);}
void gaw_recompiled_entity_call(uint8_t bank,uint16_t cpu_address,GawEntity*entity){(void)gaw_sms_compat_entity_call(bank,cpu_address,entity);}
void gaw_recompiled_world_call(uint8_t bank,uint16_t cpu_address){(void)gaw_sms_compat_world_call(bank,cpu_address);}
