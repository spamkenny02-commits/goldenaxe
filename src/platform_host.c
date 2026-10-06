#include "include/gaw_core.h"
#include "include/gaw_platform.h"

static uint8_t host_pad;
static uint8_t host_entropy;
static uint8_t host_sram[0x8000];
static unsigned host_frame, pulse_start, pulse_end;
static uint8_t pulse_bits;
void gaw_platform_init(void) { host_pad = 0; host_entropy = 0x5A; host_frame=0; pulse_start=pulse_end=0; pulse_bits=0; }
void gaw_platform_wait_vblank(void) { ++host_frame; if(pulse_start && host_frame>=pulse_start && host_frame<pulse_end) host_pad=pulse_bits; else if(pulse_start && host_frame>=pulse_end) host_pad=0; gaw_vblank_tick(host_pad); }
uint8_t gaw_platform_read_pad_sms_bits(void) { return host_pad; }
void gaw_platform_audio_command(uint8_t command) { (void)command; }
uint8_t gaw_platform_entropy8(void) { uint8_t v=host_entropy; host_entropy=(uint8_t)(host_entropy*33u+17u); return v; }
void gaw_platform_entity_resource_load(uint8_t resource_id) { (void)resource_id; }
void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot){(void)type;(void)gfx_slot;}
void gaw_platform_world_rebuilt(void) {}
void gaw_platform_world_scroll_begin(void) {}
void gaw_platform_world_scroll_end(void) {}
void gaw_platform_inventory_refresh(void) {}
void gaw_platform_player_special_effect(uint8_t effect_id) { (void)effect_id; }
void gaw_platform_show_world_map(void) {}
void gaw_platform_world_message(uint16_t table_addr,uint8_t saved_cell){(void)table_addr;(void)saved_cell;}
void gaw_platform_player_transition_frame(void) {}
uint8_t gaw_platform_sram_read(uint16_t offset){return host_sram[offset&0x7FFFu];}
void gaw_platform_sram_write(uint16_t offset,uint8_t value){host_sram[offset&0x7FFFu]=value;}

/* Test/debug helper; not part of the console backend API. */
void gaw_host_set_pad(uint8_t held_bits) { host_pad = held_bits & 0x3F; }
void gaw_host_set_entropy(uint8_t value) { host_entropy=value; }

void gaw_host_pulse_pad(unsigned start_frame,unsigned duration,uint8_t bits){pulse_start=start_frame;pulse_end=start_frame+duration;pulse_bits=(uint8_t)(bits&0x3Fu);}
unsigned gaw_host_frame_count(void){return host_frame;}
