#include "include/gaw_assets.h"
#include "include/gaw_ui.h"
#include "include/gaw_core.h"
#include "include/gaw_platform.h"

static uint8_t host_pad;
static uint8_t host_entropy;
static uint8_t host_sram[0x8000];
static unsigned host_frame, pulse_start, pulse_end;
static uint8_t pulse_bits;
static unsigned pause_frame;
static void (*frame_observer)(void);
static unsigned event_frame[256],event_count,event_next;
static uint8_t event_bits[256];
static uint8_t entropy_values[64];
static unsigned entropy_count,entropy_next;
static uint16_t sound_trace[256];
static unsigned sound_count;
void gaw_platform_sound_write(uint8_t port,uint8_t value){if(sound_count<256u)sound_trace[sound_count]=(uint16_t)(((uint16_t)port<<8)|value);++sound_count;}
void gaw_host_clear_sound_trace(void){sound_count=0;}
unsigned gaw_host_sound_trace(uint16_t *values,unsigned capacity){unsigned n=sound_count<256u?sound_count:256u;if(n>capacity)n=capacity;for(unsigned i=0;i<n;++i)values[i]=sound_trace[i];return sound_count;}
void gaw_platform_init(void) { host_pad = 0; host_entropy = 0x5A; host_frame=0; pulse_start=pulse_end=0; pulse_bits=0;pause_frame=0;frame_observer=0;event_count=event_next=0;entropy_count=entropy_next=0;sound_count=0; }
void gaw_platform_wait_vblank(void) { ++host_frame;if(pause_frame==host_frame)gaw_nmi_pause(); if(pulse_start && host_frame>=pulse_start && host_frame<pulse_end) host_pad=pulse_bits; else if(pulse_start && host_frame>=pulse_end) host_pad=0; while(event_next<event_count && host_frame>=event_frame[event_next])host_pad=event_bits[event_next++]; gaw_vblank_tick(host_pad);if(frame_observer)frame_observer(); }
uint8_t gaw_platform_read_pad_sms_bits(void) { return host_pad; }
uint8_t gaw_platform_entropy8(void) { if(entropy_next<entropy_count)return entropy_values[entropy_next++];uint8_t v=host_entropy; host_entropy=(uint8_t)(host_entropy*33u+17u); return v; }
void gaw_platform_entity_resource_load(uint8_t resource_id) { gaw_assets_load_item(resource_id,0x7780u); }
void gaw_platform_map_entity_resource_load(uint8_t type,uint8_t gfx_slot){gaw_assets_load_map_entity(type,gfx_slot);}
void gaw_platform_world_rebuilt(void) {gaw_ui_upload_name_table();}
void gaw_platform_inventory_refresh(void) {gaw_assets_update_inventory();}
void gaw_platform_world_message(uint16_t resource,uint8_t saved_cell){(void)saved_cell;gaw_ui_show_message(resource);}
uint8_t gaw_platform_sram_read(uint16_t offset){return host_sram[offset&0x7FFFu];}
void gaw_platform_sram_write(uint16_t offset,uint8_t value){host_sram[offset&0x7FFFu]=value;}

/* Test/debug helper; not part of the console backend API. */
void gaw_host_set_pad(uint8_t held_bits) { host_pad = held_bits & 0x3F; }
void gaw_host_set_entropy(uint8_t value) { host_entropy=value; }

void gaw_host_pulse_pad(unsigned start_frame,unsigned duration,uint8_t bits){pulse_start=start_frame;pulse_end=start_frame+duration;pulse_bits=(uint8_t)(bits&0x3Fu);}
unsigned gaw_host_frame_count(void){return host_frame;}
void gaw_host_queue_pad(unsigned frame,uint8_t bits){if(event_count<256u){event_frame[event_count]=frame;event_bits[event_count++]=(uint8_t)(bits&0x3Fu);}}
void gaw_host_set_entropy_sequence(const uint8_t *values,unsigned count){entropy_count=count<64u?count:64u;entropy_next=0;for(unsigned i=0;i<entropy_count;++i)entropy_values[i]=values[i];}
void gaw_host_queue_pause(unsigned frame){pause_frame=frame;}
void gaw_host_set_frame_observer(void (*observer)(void)){frame_observer=observer;}
