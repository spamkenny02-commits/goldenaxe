#include <string.h>
#include "include/gaw_core.h"
#include "include/gaw_entity.h"
#include "include/gaw_player.h"
#include "include/gaw_recompiled.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_tables.h"
#include "include/gaw_sms_compat.h"
#include "include/gaw_world.h"
#include "include/gaw_world_progress.h"
#include "include/gaw_ui.h"
#include "include/gaw_effects.h"

static void edge_update(uint16_t held_addr, uint16_t pressed_addr, uint8_t now) {
    uint8_t old = gaw_ram_read8(held_addr);
    gaw_ram_write8(held_addr, now);
    gaw_ram_write8(pressed_addr, (uint8_t)(now & (now ^ old)));
}

void gaw_reset(void) {
    gaw_ram_reset_like_z80();
    gaw_video_reset();
    gaw_platform_init();
    gaw_save_initialize_native();
    gaw_video_initialize_native();
    gaw_wait_frame();
}

void gaw_nmi_pause(void) {
    if (gaw_ram_read8(RAM_PAUSE_NMI_COUNTER) == 0)
        gaw_ram_write8(RAM_PAUSE_NMI_COUNTER, 0x14);
}

void gaw_vblank_tick(uint8_t held_bits) {
    uint8_t pause = 0;
    uint8_t counter = gaw_ram_read8(RAM_PAUSE_NMI_COUNTER);
    if (counter != 0) {
        gaw_ram_write8(RAM_PAUSE_NMI_COUNTER, (uint8_t)(counter - 1u));
        pause = 1;
    }
    edge_update(RAM_PAUSE_HELD, RAM_PAUSE_PRESSED, pause);
    edge_update(RAM_INPUT_HELD, RAM_INPUT_PRESSED, (uint8_t)(held_bits & 0x3Fu));

    uint8_t timer = gaw_ram_read8(RAM_TIMER_C030);
    if (timer != 0) gaw_ram_write8(RAM_TIMER_C030, (uint8_t)(timer - 1u));
    gaw_ram_write8(RAM_FRAME_COUNTER, (uint8_t)(gaw_ram_read8(RAM_FRAME_COUNTER) + 1u));
    gaw_ram_write8(RAM_VBLANK_WAIT_FLAG, 0);
}

void gaw_wait_frame(void) {
    /* $0BA7-$0BB3 sets C02E and sleeps until VBlank clears it. */
    gaw_ram_write8(RAM_VBLANK_WAIT_FLAG, 1);
    gaw_platform_wait_vblank();
}

void gaw_world_select_callback(void) {
    /* Faithful RAM-visible part of $5B20. Mapper writes disappear in C. */
    gaw_ram_write16le(0xDCE0, 0xC0B0);
    gaw_ram_write16le(0xDCE2, 0xC0B0);
    gaw_ram_write16le(0xDCE4, 0xC0B0);
    gaw_ram_write16le(0xC062, gaw_ram_read16le(0xC060));
    gaw_ram_write8(0xC064, gaw_ram_read8(0xC30A));

    uint16_t cell = gaw_ram_read16le(RAM_WORLD_CELL_ID);
    if (cell < 512)
        gaw_ram_write16le(RAM_WORLD_CALLBACK, gaw_world_callback_targets[cell]);
    else
        gaw_ram_write16le(RAM_WORLD_CALLBACK, 0); /* impossible in known original range */

    if (gaw_ram_read8(0xC0A2) & 0x80u)
        gaw_ram_write8(0xC0A8, 2);
}


static void gaw_world_audio_select_native(void);
static void world_explicit_progress_set(uint16_t cell,uint8_t bit){uint16_t a=(uint16_t)(0xC100u+(uint8_t)cell);gaw_ram_write8(a,(uint8_t)(gaw_ram_read8(a)|(uint8_t)(1u<<bit)));}
static int world_explicit_progress_test_and_set(uint8_t bit){uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID),a=(uint16_t)(0xC100u+(uint8_t)cell);uint8_t m=(uint8_t)(1u<<bit),old=gaw_ram_read8(a);gaw_ram_write8(a,(uint8_t)(old|m));return (old&m)!=0;}
static void world_spawn_type14(void){for(unsigned i=9u;i<15u;++i){GawEntity*e=gaw_entity(i);if(e->raw[ENT_TYPE])continue;memset(e->raw,0,GAW_ENTITY_SIZE);e->raw[ENT_TYPE]=14;e->raw[0x11]=0x60;e->raw[0x13]=0x80;return;}}
static void world_open_gate5(uint16_t cell){if(gaw_ram_read8(0xDC18u)==0)return;world_explicit_progress_set(cell,5);gaw_ram_write16le(0xDC17u,0);gaw_ram_write8(0xDE08u,0xA5u);gaw_world_finalize_transition();}
static void world_open_gate6(uint16_t cell){if(gaw_ram_read8(0xDC41u)==0)return;world_explicit_progress_set(cell,6);uint8_t lo=(uint8_t)cell;world_explicit_progress_set((uint16_t)((lo&0xF0u)|((lo-1u)&0x0Fu)),7);gaw_ram_write8(0xDC31u,0x18u);gaw_ram_write8(0xDC41u,0);gaw_ram_write8(0xDC51u,0x19u);gaw_ram_write8(0xDE08u,0xA5u);gaw_world_finalize_transition();}
static void world_open_gate7(uint16_t cell){if(gaw_ram_read8(0xDC4Eu)==0)return;world_explicit_progress_set(cell,7);uint8_t lo=(uint8_t)cell;world_explicit_progress_set((uint16_t)((lo&0xF0u)|((lo+1u)&0x0Fu)),6);gaw_ram_write8(0xDC3Eu,0x22u);gaw_ram_write8(0xDC4Eu,0);gaw_ram_write8(0xDC5Eu,0x23u);gaw_ram_write8(0xDE08u,0xA5u);gaw_world_finalize_transition();}
static void world_callback_5e57_body(void){gaw_world_progress_restore_for_current_cell();uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(gaw_ram_read8(0xDC17u)==0x3Du)world_open_gate5(cell);if(gaw_ram_read8(0xDC31u)==0x33u)world_open_gate6(cell);if(gaw_ram_read8(0xDC3Eu)==0x38u)world_open_gate7(cell);}

/* RAM-visible part of $18E9. The original stores presence for the eight
   local C600 slots in C200[current cell] before changing cells. */
static void world_save_local_presence(void){
    uint8_t mask=0;
    for(unsigned i=0;i<8u;++i) mask=(uint8_t)((mask<<1)|(gaw_ram_read8((uint16_t)(0xC600u+i*0x30u))!=0));
    gaw_ram_write8((uint16_t)(0xC200u+(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID)),mask);
}
/* $0B12 has VDP writes as well; these are the RAM-visible side effects used
   by the room-entry callbacks. Physical VDP state is a platform concern. */
static void world_transition_display_reset_ram(void){
    memset(gaw_ram_ptr(0xDCC0u),0,0x20u);
    gaw_ram_write8(0xC010u,(uint8_t)(gaw_ram_read8(0xC010u)&0xEFu));
    gaw_ram_write8(0xC011u,(uint8_t)(gaw_ram_read8(0xC011u)&0xBFu));
    gaw_ram_write8(0xDD40u,0xD0u);
    gaw_ui_display_reset();
}
/* $65E1: return from a linked/interior room to the cell saved in C0BB. */
static void world_return_to_saved_cell(void){
    gaw_ram_write8(0xC037u,0);
    uint16_t target=gaw_ram_read16le(0xC0BBu);
    world_save_local_presence();
    gaw_ram_write16le(RAM_WORLD_CELL_ID,target);
    gaw_ram_write8(0xC311u,gaw_ram_read8(0xC0BDu));
    gaw_ram_write8(0xC313u,gaw_ram_read8(0xC0BEu));
    gaw_ram_write8(0xC30Au,1u);
    gaw_ram_write8(0xC01Du,8u);
    world_transition_display_reset_ram();
}
/* $1C97. */
static void world_clear_cell_presence_and_aux(void){
    memset(gaw_ram_ptr(0xC200u),0xFF,0x100u);
    memset(gaw_ram_ptr(0xDCF0u),0,0x10u);
}
/* $654D: ten callback-table entries use this fixed-position return trigger. */
static void gaw_world_callback_654d_native(void){
    if((gaw_ram_read16le(0xC060u)&0xFFF8u)!=0x0518u)return;
    world_return_to_saved_cell();
    world_clear_cell_presence_and_aux();
}
/* $65D0: nine callback-table entries plus many scripted callbacks share the
   same return trigger. */
static void gaw_world_callback_65d0_native(void){
    if((gaw_ram_read8(0xC0A6u)&0x30u)!=0x30u)return;
    if(gaw_ram_read16le(0xC060u)!=0x051Cu)return;
    world_return_to_saved_cell();
}

/* $5CFB. Returns true when the Z80 would POP its caller return address and
   therefore terminate the callback immediately after changing rooms. */
static int world_trigger_linked_room(uint16_t position,uint8_t low_cell){
    if((gaw_ram_read8(0xC0A6u)&0x30u)!=0x30u)return 0;
    if(gaw_ram_read16le(0xC060u)!=position)return 0;
    uint16_t old=gaw_ram_read16le(RAM_WORLD_CELL_ID);
    world_save_local_presence();
    gaw_ram_write16le(RAM_WORLD_CELL_ID,(uint16_t)((old&0xFF00u)|low_cell));
    /* RAM-visible tail of $1F78/$0B24. */
    gaw_ram_write8(0xDE08u,0xA6u);
    gaw_ram_write8(0xC010u,(uint8_t)(gaw_ram_read8(0xC010u)&0xEFu));
    gaw_ram_write8(0xC011u,(uint8_t)(gaw_ram_read8(0xC011u)&0xBFu));
    gaw_ram_write8(0xDD40u,0xD0u);
    gaw_world_reload_after_scroll();
    unsigned found=160u;
    for(unsigned i=0;i<160u;++i)if(gaw_ram_read8((uint16_t)(0xDC00u+i))==0x0Cu){found=i;break;}
    if(found==160u){gaw_ram_write8(0xC313u,0x80u);gaw_ram_write8(0xC311u,0x58u);}
    else {gaw_ram_write8(0xC313u,(uint8_t)(((found&0x0Fu)<<4)+8u));gaw_ram_write8(0xC311u,(uint8_t)((found&0xF0u)+0x10u));}
    gaw_ram_write8(0xC30Au,1u);gaw_ram_write8(0xC01Du,8u);
    return 1;
}
typedef struct {uint16_t target,position;uint8_t cell,before_gate,after_gate;} WorldLinkCallback;
static const WorldLinkCallback world_link_callbacks[]={
 {0xB3EBu,0x01B0u,0x38u,0,0},{0xB402u,0x0184u,0x4Eu,0,0},
 {0xB444u,0x0298u,0x1Cu,0,1},{0xB45Fu,0x01B0u,0x69u,0,0},
 {0xB47Au,0x0318u,0x7Bu,0,1},{0xB486u,0x0318u,0x6Au,0,0},
 {0xB4B5u,0x0398u,0x6Cu,1,0},{0xB4C1u,0x029Cu,0x19u,0,0},
 {0xB4D6u,0x028Cu,0x62u,0,0},{0xB4F4u,0x0290u,0x4Bu,0,0},
 {0xB51Fu,0x0184u,0x88u,0,0},{0xB528u,0x029Cu,0x38u,0,0},
 {0xB57Du,0x0218u,0x3Cu,0,0},{0xB59Eu,0x0430u,0xA3u,0,1},
 {0xB5B1u,0x0184u,0xA8u,0,0},{0xB5DEu,0x032Cu,0x92u,0,0},
 {0xB5EDu,0x0408u,0xD7u,1,0},{0xB60Au,0x0298u,0x98u,0,0},
 {0xB61Au,0x042Cu,0xE8u,1,0},{0xB656u,0x029Cu,0xCBu,0,0},
 {0xB6A6u,0x0184u,0xEBu,0,0},{0xB6AFu,0x0318u,0x9Eu,0,1},
 {0xB6C9u,0x0298u,0xA6u,0,0},{0xB6D2u,0x0298u,0xFAu,0,0},
 {0xB6E9u,0x02A8u,0xE7u,1,0},{0xB719u,0x0298u,0xE2u,0,0},
 {0xB722u,0x031Cu,0xAAu,0,0}
};
static int world_run_link_callback(uint16_t target){
    for(unsigned i=0;i<sizeof world_link_callbacks/sizeof world_link_callbacks[0];++i){
        const WorldLinkCallback *w=&world_link_callbacks[i];if(w->target!=target)continue;
        if(w->before_gate)gaw_world_callback_5d4c_native();
        if(world_trigger_linked_room(w->position,w->cell))return 1;
        if(w->after_gate)gaw_world_callback_5d4c_native();
        return 1;
    }
    return 0;
}

typedef struct {uint16_t target,position;} WorldProgressGateCallback;
static const WorldProgressGateCallback world_progress_gate_callbacks[]={
 {0xB3F4u,0x035Cu},{0xB3FBu,0x0168u},{0xB48Fu,0x014Cu},
 {0xB4E6u,0x0168u},{0xB518u,0x0168u},{0xB5AAu,0x014Cu},
 {0xB639u,0x014Cu},{0xB669u,0x014Cu},{0xB69Fu,0x0168u},
 {0xB6DBu,0x0168u},{0xB6E2u,0x014Cu},{0xB72Bu,0x014Cu},
 {0xB74Au,0x014Cu}
};
/* $5E45 wrappers: action+position gated one-shot progression restoration. */
static int world_run_progress_gate_callback(uint16_t target){
    for(unsigned i=0;i<sizeof world_progress_gate_callbacks/sizeof world_progress_gate_callbacks[0];++i){
        const WorldProgressGateCallback*w=&world_progress_gate_callbacks[i];if(w->target!=target)continue;
        if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u && gaw_ram_read16le(0xC060u)==w->position){
            if(!gaw_world_progress_test_and_set())world_callback_5e57_body();
        }
        return 1;
    }
    return 0;
}

typedef struct {uint16_t target,position;} WorldFinalizeCallback;
static const WorldFinalizeCallback world_finalize_callbacks[]={
 {0xB420u,0x0168u},{0xB49Fu,0x014Cu},{0xB4DFu,0x0168u},
 {0xB691u,0x034Cu},{0xB6BBu,0x0168u}
};
/* $5E29 wrappers. */
static int world_run_finalize_callback(uint16_t target){
    for(unsigned i=0;i<sizeof world_finalize_callbacks/sizeof world_finalize_callbacks[0];++i){
        const WorldFinalizeCallback*w=&world_finalize_callbacks[i];if(w->target!=target)continue;
        if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u && gaw_ram_read16le(0xC060u)==w->position){
            if(!gaw_world_progress_test_and_set()){gaw_world_finalize_transition();gaw_ram_write8(0xDE08u,0xA8u);}
        }
        return 1;
    }
    return 0;
}


typedef struct {uint16_t target,position;uint8_t gate;} WorldFinalizeGateCallback;
static const WorldFinalizeGateCallback world_finalize_gate_callbacks[]={
 {0xB450u,0x0168u,3u},{0xB54Eu,0x0358u,2u},{0xB557u,0x0168u,0u},
 {0xB670u,0x014Cu,3u},{0xB6F5u,0x0358u,0u}
};
/* $5E0D wrappers: one-shot finalize followed by one of the three persistent
   gate-opening routines selected through the original $5EC5 table. */
static int world_run_finalize_gate_callback(uint16_t target){
 for(unsigned i=0;i<sizeof world_finalize_gate_callbacks/sizeof world_finalize_gate_callbacks[0];++i){const WorldFinalizeGateCallback*w=&world_finalize_gate_callbacks[i];if(w->target!=target)continue;
  if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u && gaw_ram_read16le(0xC060u)==w->position && !gaw_world_progress_test_and_set()){
   gaw_world_finalize_transition();uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(w->gate<2u)world_open_gate5(cell);else if(w->gate==2u)world_open_gate6(cell);else world_open_gate7(cell);
  }return 1;
 }return 0;
}


typedef struct {uint16_t target;uint8_t gate;} WorldDirectGateCallback;
static const WorldDirectGateCallback world_direct_gate_callbacks[]={{0xB427u,2u},{0xB58Fu,0u},{0xB5E7u,0u},{0xB649u,3u}};
/* Pure $5EB1 wrappers. */
static int world_run_direct_gate_callback(uint16_t target){for(unsigned i=0;i<sizeof world_direct_gate_callbacks/sizeof world_direct_gate_callbacks[0];++i){const WorldDirectGateCallback*w=&world_direct_gate_callbacks[i];if(w->target!=target)continue;if(gaw_ram_read8(0xC0A2u)==0){gaw_ram_write8(0xC0A2u,0x80u);uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(w->gate<2u)world_open_gate5(cell);else if(w->gate==2u)world_open_gate6(cell);else world_open_gate7(cell);}return 1;}return 0;}


/* Two single-use wrappers around $5E29. */
static int world_run_finalize_special_callback(uint16_t target){
 if(target!=0xB586u && target!=0xB698u)return 0;
 uint16_t pos=(target==0xB586u)?0x0168u:0x0168u;
 if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u && gaw_ram_read16le(0xC060u)==pos && !gaw_world_progress_test_and_set()){
  gaw_world_finalize_transition();gaw_ram_write8(0xDE08u,0xA8u);
  if(target==0xB586u)world_explicit_progress_set(0x017Bu,2u);else world_spawn_type14();
 }
 return 1;
}


static int world_try_finalize_at(uint16_t pos){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return 0;if(gaw_world_progress_test_and_set())return 0;gaw_world_finalize_transition();gaw_ram_write8(0xDE08u,0xA8u);return 1;}
static void world_direct_gate(uint8_t gate){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(gate<2u)world_open_gate5(cell);else if(gate==2u)world_open_gate6(cell);else world_open_gate7(cell);}
static void world_try_finalize_gate_at(uint16_t pos,uint8_t gate){if(world_try_finalize_at(pos)){uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(gate<2u)world_open_gate5(cell);else if(gate==2u)world_open_gate6(cell);else world_open_gate7(cell);}}
static void world_try_finalize_explicit_at(uint16_t pos,uint8_t low_cell){if(world_try_finalize_at(pos)){world_explicit_progress_set((uint16_t)(0x0100u|low_cell),2u);gaw_ram_write8(0xDE08u,0xA8u);}}
static void gaw_world_callback_5e75_native(void);
static void gaw_world_callback_5ecd_native(void);
/* Small Bxxx scripts made solely from helpers that are already native. */
static int world_run_composed_callback(uint16_t target){switch(target){
 case 0xB40Bu:world_direct_gate(2);(void)world_trigger_linked_room(0x01B0u,0x2Au);return 1;
 case 0xB4A6u:(void)world_try_finalize_at(0x0168u);(void)world_trigger_linked_room(0x0414u,0x5Au);return 1;
 case 0xB4CAu:(void)world_try_finalize_at(0x0168u);world_direct_gate(3);return 1;
 case 0xB531u:if(!world_trigger_linked_room(0x0184u,0x3Eu))gaw_world_callback_5e75_native();return 1;
 case 0xB53Du:if(!world_trigger_linked_room(0x0424u,0x4Du))world_try_finalize_gate_at(0x014Cu,0);return 1;
 case 0xB5CBu:if(!world_trigger_linked_room(0x029Cu,0xCCu))gaw_world_callback_5e75_native();return 1;
 case 0xB65Fu:if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u&&gaw_ram_read16le(0xC060u)==0x0168u&&!gaw_world_progress_test_and_set())world_callback_5e57_body();gaw_world_callback_5ecd_native();return 1;
 case 0xB732u:world_direct_gate(3);world_try_finalize_explicit_at(0x014Cu,0xC8u);return 1;
 default:return 0;}}


/* $5C96: position/action gated persistent gate-bit setup. DE encodes the
   target cell in E and which neighbor bits to set in D. */
static void world_try_progress_bits_at(uint16_t pos,uint16_t spec){
 if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos||gaw_world_progress_test_and_set())return;
 uint8_t cell=(uint8_t)spec,flags=(uint8_t)(spec>>8);
 if(flags&1u)world_explicit_progress_set((uint16_t)(0x0100u|cell),5u);
 if(flags&4u){world_explicit_progress_set((uint16_t)(0x0100u|cell),6u);world_explicit_progress_set((uint16_t)(0x0100u|((cell&0xF0u)|((cell-1u)&0x0Fu))),7u);}
 if(flags&8u){world_explicit_progress_set((uint16_t)(0x0100u|cell),7u);world_explicit_progress_set((uint16_t)(0x0100u|((cell&0xF0u)|((cell+1u)&0x0Fu))),6u);}
 gaw_ram_write8(0xDE08u,0xA5u);gaw_world_finalize_transition();
}
static int world_run_progress_bits_callback(uint16_t target){switch(target){
 case 0xB5BAu:world_try_progress_bits_at(0x014Cu,0x04D8u);return 1;
 case 0xB62Fu:world_try_progress_bits_at(0x014Cu,0x049Du);return 1;
 case 0xB740u:world_try_progress_bits_at(0x0168u,0x04EBu);return 1;
 case 0xB679u:world_try_progress_bits_at(0x0168u,0x01BCu);gaw_world_callback_5d4c_native();return 1;
 case 0xB506u:world_try_progress_bits_at(0x014Cu,0x0872u);(void)world_trigger_linked_room(0x029Cu,0x53u);return 1;
 case 0xB707u:world_try_progress_bits_at(0x014Cu,0x04D6u);(void)world_trigger_linked_room(0x0418u,0xCBu);return 1;
 default:return 0;}}


static void world_explicit_progress_clear(uint8_t cell,uint8_t bit){uint16_t a=(uint16_t)(0xC100u+cell);gaw_ram_write8(a,(uint8_t)(gaw_ram_read8(a)&(uint8_t)~(1u<<bit)));}
/* $5F2B: temporary gate opening while all required callback flags are active. */
static void world_temp_gate_begin(uint8_t gate){
 uint8_t a=gaw_ram_read8(0xC0A2u);if((gaw_ram_read8(0xC0A6u)&0xB0u)!=0xB0u||a==0||a==0x80u||gaw_ram_read8(0xC0A8u)!=0)return;
 gaw_ram_write8(0xC0A8u,1u);gaw_ram_write8(0xC0A9u,gate);uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID);
 if(gate<2u){world_explicit_progress_clear(cell,5u);gaw_ram_write8(0xDC17u,0x3Du);gaw_ram_write8(0xDC18u,0x3Du);}
 else if(gate==2u){if(gaw_ram_read8(0xDC31u)==0x33u)return;world_explicit_progress_clear(cell,6u);world_explicit_progress_clear((uint8_t)((cell&0xF0u)|((cell-1u)&0x0Fu)),7u);gaw_ram_write8(0xDC31u,0x33u);gaw_ram_write8(0xDC41u,0x34u);gaw_ram_write8(0xDC51u,0x35u);}
 else {world_explicit_progress_clear(cell,7u);world_explicit_progress_clear((uint8_t)((cell&0xF0u)|((cell+1u)&0x0Fu)),6u);gaw_ram_write8(0xDC3Eu,0x38u);gaw_ram_write8(0xDC4Eu,0x39u);gaw_ram_write8(0xDC5Eu,0x3Au);}
 gaw_ram_write8(0xDE08u,0xA5u);gaw_world_finalize_transition();
}
/* $5F0D: when C0A2 drops to zero, commit the temporary gate persistently. */
static void world_temp_gate_commit(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);if(gaw_ram_read8(0xC0A8u)!=1u)return;gaw_ram_write8(0xC0A8u,2u);uint8_t gate=gaw_ram_read8(0xC0A9u);uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);if(gate<2u)world_open_gate5(cell);else if(gate==2u)world_open_gate6(cell);else world_open_gate7(cell);}
static int world_run_temp_gate_callback(uint16_t target){switch(target){
 case 0xB433u:world_temp_gate_begin(3);world_temp_gate_commit();world_try_finalize_explicit_at(0x014Cu,0x2Au);return 1;
 case 0xB468u:world_try_progress_bits_at(0x0168u,0x0538u);world_temp_gate_begin(2);world_temp_gate_commit();return 1;
 case 0xB566u:world_temp_gate_begin(2);(void)world_trigger_linked_room(0x0318u,0x55u);return 1;
 case 0xB595u:world_temp_gate_begin(2);world_temp_gate_commit();return 1;
 case 0xB5F9u:world_temp_gate_begin(2);world_temp_gate_commit();(void)world_trigger_linked_room(0x01B0u,0xEBu);return 1;
 case 0xB640u:world_temp_gate_begin(3);world_temp_gate_commit();return 1;
 case 0xB686u:world_temp_gate_begin(2);world_direct_gate(0);return 1;
 default:return 0;}}

typedef struct {uint16_t target,position;uint8_t key;} WorldKeyRoomCallback;
static const WorldKeyRoomCallback world_key_room_callbacks[]={
#include "world_key_room_callbacks.inc"
};
/* $6560: keyed/special room entry. $6589 is deliberately byte-indexed. */
static void world_try_enter_key_room(uint16_t position,uint8_t key){
 static const uint8_t target_low[11]={0x1C,0xE4,0x71,0xF8,0xF0,0x86,0x87,0xDB,0xEA,0xFC,0x8D};
 if((gaw_ram_read8(0xC0A6u)&0x30u)!=0x30u||gaw_ram_read16le(0xC060u)!=position||key>=sizeof target_low)return;
 gaw_ram_write8(0xC037u,key);uint16_t old=gaw_ram_read16le(RAM_WORLD_CELL_ID);gaw_ram_write16le(0xC0BBu,old);world_save_local_presence();gaw_ram_write16le(RAM_WORLD_CELL_ID,(uint16_t)(0x0100u|target_low[key]));
 gaw_ram_write8(0xC0BDu,gaw_ram_read8(0xC311u));gaw_ram_write8(0xC0BEu,gaw_ram_read8(0xC313u));gaw_ram_write8(0xC311u,0x98u);gaw_ram_write8(0xC313u,0x88u);gaw_ram_write8(0xC30Au,0);gaw_ram_write8(0xC01Du,8u);world_transition_display_reset_ram();
 gaw_ram_write16le(0xC0C4u,gaw_ram_read16le(RAM_WORLD_CELL_ID));gaw_ram_write8(0xC313u,0x80u);world_clear_cell_presence_and_aux();
}
static int world_run_key_room_callback(uint16_t target){for(unsigned i=0;i<sizeof world_key_room_callbacks/sizeof world_key_room_callbacks[0];++i){const WorldKeyRoomCallback*w=&world_key_room_callbacks[i];if(w->target!=target)continue;world_try_enter_key_room(w->position,w->key);return 1;}return 0;}

typedef struct {uint16_t target,position;uint8_t cell;} WorldRoomEntryAction;
static const WorldRoomEntryAction world_room_entry_actions[]={
#include "world_room_callbacks.inc"
};
static const uint16_t world_room_entry_targets[]={
#include "world_room_callback_targets.inc"
};
static const uint16_t world_room_finalize_targets[]={
#include "world_room_finalize_targets.inc"
};
static int u16_in_list(uint16_t v,const uint16_t *p,unsigned n){for(unsigned i=0;i<n;++i)if(p[i]==v)return 1;return 0;}
/* $6594/$65A4: standard overworld -> interior room entry. */
static void world_try_enter_room(uint16_t position,uint8_t low_cell){
 if((gaw_ram_read8(0xC0A6u)&0x30u)!=0x30u||gaw_ram_read16le(0xC060u)!=position)return;
 uint16_t old=gaw_ram_read16le(RAM_WORLD_CELL_ID);gaw_ram_write16le(0xC0BBu,old);world_save_local_presence();gaw_ram_write16le(RAM_WORLD_CELL_ID,low_cell);
 gaw_ram_write8(0xC0BDu,gaw_ram_read8(0xC311u));gaw_ram_write8(0xC0BEu,gaw_ram_read8(0xC313u));gaw_ram_write8(0xC311u,0x98u);gaw_ram_write8(0xC313u,0x88u);gaw_ram_write8(0xC30Au,0);gaw_ram_write8(0xC01Du,8u);world_transition_display_reset_ram();
}
/* $5FB1: after-room one-shot finalization used by nine wrappers. */
static void world_callback_5fb1_native(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);if(gaw_world_progress_test_and_set())return;gaw_ram_write8(0xDE08u,0xA8u);gaw_world_finalize_transition();}
static int world_run_room_entry_callback(uint16_t target){
 if(!u16_in_list(target,world_room_entry_targets,sizeof world_room_entry_targets/sizeof world_room_entry_targets[0]))return 0;
 for(unsigned i=0;i<sizeof world_room_entry_actions/sizeof world_room_entry_actions[0];++i){const WorldRoomEntryAction*w=&world_room_entry_actions[i];if(w->target==target)world_try_enter_room(w->position,w->cell);}
 if(u16_in_list(target,world_room_finalize_targets,sizeof world_room_finalize_targets/sizeof world_room_finalize_targets[0]))world_callback_5fb1_native();
 return 1;
}

static void world_try_script_marker(uint16_t pos,uint8_t value);
static void hud_update_phase(uint8_t phase);
static int world_try_message(uint16_t pos,uint16_t table_addr);
static void script_wait_message(void);
static void world_direct_message(uint16_t resource){gaw_ui_show_message(resource);script_wait_message();}
static int world_try_cond_message(uint16_t pos,uint16_t a,uint16_t b){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return 0;world_direct_message((gaw_ram_read8(0xC0D7u)&0x80u)?b:a);return 1;}
static int world_try_ad55_special(uint16_t pos){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return 0;if(gaw_ram_read8(0xC0D2u)==0){world_direct_message(0xA077u);return 1;}if(gaw_ram_read8(0xC0F7u)!=0){world_direct_message(0xA17Fu);return 1;}gaw_ram_write8(0xC0F7u,1);uint8_t cur=gaw_ram_read8(0xC0DDu);unsigned n=100u;if((unsigned)cur+n>255u)n=255u-cur;gaw_ram_write16le(0xDCE4u,(uint16_t)n);for(unsigned i=0;i<n;++i){gaw_ram_write8(0xC0DDu,(uint8_t)(gaw_ram_read8(0xC0DDu)+1u));gaw_ram_write8(0xDE08u,0x95u);gaw_ram_write8(0xC045u,0x83u);hud_update_phase(3u);}do{gaw_wait_frame();}while((gaw_ram_read8(RAM_INPUT_HELD)&0x3Fu)==0);gaw_world_finalize_transition();return 1;}
static int world_run_special_message_callback(uint16_t target){
 if(target==0xACB9u){if(gaw_ram_read8(0xC0BBu)==0xCEu){if(world_try_cond_message(0x025Cu,0xA7CEu,0xAC65u))return 1;if(world_try_cond_message(0x02E0u,0xA852u,0xACB5u))return 1;if(world_try_cond_message(0x0344u,0xA887u,0xACE3u))return 1;}else{if(world_try_message(0x025Cu,0xACDFu))return 1;if(world_try_message(0x02E0u,0xACE8u))return 1;if(world_try_message(0x0344u,0xACF1u))return 1;}gaw_world_callback_65d0_native();return 1;}
 if(target==0xAD55u){if(gaw_ram_read8(0xC0BBu)==0x22u){if(world_try_ad55_special(0x02D4u))return 1;}else if(world_try_message(0x02D4u,0xAD69u))return 1;gaw_world_callback_65d0_native();return 1;}return 0;}

static void world_direct_message(uint16_t resource);
static uint8_t world_player_tile_index(void){uint8_t row=(uint8_t)((gaw_ram_read8(0xC313u)&0xF0u)>>4),col=(uint8_t)((gaw_ram_read8(0xC311u)-0x10u)&0xF0u);return (uint8_t)(col|row);}
/* $62A9. Return true when its POP AF consumed the callback return. */
static int world_try_context_message(uint16_t pos){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return 0;if(gaw_ram_read8((uint16_t)(0xDC00u+world_player_tile_index()))==0x31u)return 0;if((uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID)==0x4Fu){if(gaw_ram_read8(0xC0E4u)==0)return 1;world_direct_message(0x62E9u);}else world_direct_message(0x62F8u);return 1;}
/* $61F4. */
static int world_try_d4_message(void){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=0x01E0u||gaw_ram_read8(0xDC2Au)==0x31u)return 0;world_direct_message((gaw_ram_read8(0xC0D4u)&0x80u)?0xAC1Eu:0xA52Fu);return 1;}
/* $621E. */
static int world_try_e4_message(void){if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=0x025Cu||gaw_ram_read8(0xDC37u)==0x31u)return 0;if(gaw_ram_read8(0xC0E4u)==0)world_direct_message(0x8E5Cu);else world_direct_message(0x624Cu);return 1;}
static int world_run_context_message_callback(uint16_t target){switch(target){case 0xADF2u:(void)world_try_context_message(0x01D4u);return 1;case 0xADA1u:if(world_try_d4_message())return 1;if(world_try_context_message(0x01E4u))return 1;gaw_world_callback_65d0_native();return 1;case 0xAF88u:if(world_try_context_message(0x0258u))return 1;if(world_try_e4_message())return 1;gaw_world_callback_65d0_native();return 1;default:return 0;}}

/* $667E->$6277: context-sensitive room message.  Text/tile upload is a
   platform concern; input timing and world finalization remain game logic. */
static int world_try_message(uint16_t pos,uint16_t table_addr){
    if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return 0;
    uint16_t p=table_addr;uint8_t saved=gaw_ram_read8(0xC0BBu);
    while(gaw_sms_rom_bank_read(2u,p)!=saved)p=(uint16_t)(p+3u);
    uint16_t text=(uint16_t)(gaw_sms_rom_bank_read(2u,p+1u)|((uint16_t)gaw_sms_rom_bank_read(2u,p+2u)<<8));
    world_direct_message(text);return 1;
}
static int world_run_message_callback(uint16_t target){switch(target){
 case 0xAC27u:world_try_script_marker(0x025Cu,0);world_try_script_marker(0x02C4u,1);world_try_script_marker(0x02F0u,2);if(world_try_message(0x0250u,0xAC5Eu))return 1;if(world_try_message(0x02D4u,0xAC67u))return 1;if(world_try_message(0x02E8u,0xAC70u))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xAC79u:world_try_script_marker(0x0260u,1);world_try_script_marker(0x0268u,0);world_try_script_marker(0x0270u,2);if(world_try_message(0x0250u,0xACA7u))return 1;if(world_try_message(0x02C8u,0xACB0u))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xAD19u:if(world_try_message(0x02ECu,0xAD2Fu))return 1;if(world_try_message(0x0248u,0xAD38u))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xAD79u:if(world_try_message(0x02D4u,0xAD98u))return 1;if(world_try_message(0x0344u,0xAD9Bu))return 1;if(world_try_message(0x034Cu,0xAD9Eu))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xADAEu:if(world_try_message(0x02C8u,0xADDFu))return 1;if(world_try_message(0x0254u,0xADE2u))return 1;if(world_try_message(0x0258u,0xADE5u))return 1;if(world_try_message(0x02ECu,0xADE8u))return 1;if(world_try_message(0x03E8u,0xADEBu))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xAE4Au:if(world_try_message(0x0168u,0xAE57u))return 1;gaw_world_callback_65d0_native();return 1;
 case 0xB102u:if(world_try_message(0x025Cu,0xB10Fu))return 1;gaw_world_callback_65d0_native();return 1;
 default:return 0;}}

/* $6911: scripted full-screen wave used after keyed room B0D9. */
static void world_callback_6911_native(void){
 if(gaw_ram_read8(0xC301u)==0||gaw_ram_read8(0xC0F8u)!=0)return;
 for(unsigned i=0;i<9u;++i)if((gaw_ram_read8((uint16_t)(0xC0CFu+i))&0x80u)==0)return;
 (void)gaw_world_progress_test_and_set();gaw_ram_write8(0xC0F8u,1);gaw_ram_write8(0xC01Au,0x9Fu);gaw_ram_write16le(0xC02Cu,0x0275u);gaw_ram_write8(0xC010u,(uint8_t)(gaw_ram_read8(0xC010u)|0x10u));memcpy(gaw_ram_ptr(0xD100u),gaw_ram_ptr(0xDD80u),0x40u);gaw_wait_frame();
 for(int base=8;base>=0;--base){for(unsigned j=0;j<32u;++j){uint8_t frame=gaw_ram_read8(RAM_FRAME_COUNTER);if((frame&3u)==0)gaw_ram_write8(0xDE06u,0x9Eu);int8_t d=(int8_t)base;if(frame&2u)d=(int8_t)-d;gaw_ram_write8(0xC018u,(uint8_t)d);for(unsigned k=0;k<64u;++k){uint16_t src=(uint16_t)(0xD100u+k*2u),dst=(uint16_t)(0xDD80u+k*2u);gaw_ram_write8(dst,(uint8_t)(gaw_ram_read8(src)+(uint8_t)d));}gaw_wait_frame();}}
 gaw_ram_write8(0xC018u,0);gaw_ram_write16le(0xC02Cu,0x0263u);gaw_ram_write8(0xC010u,(uint8_t)(gaw_ram_read8(0xC010u)&0xEFu));gaw_ram_write8(0xDE08u,0xA8u);gaw_world_finalize_transition();
}
static int world_run_key_wave_callback(uint16_t target){if(target!=0xB0D9u)return 0;world_try_enter_key_room(0x031Cu,6u);world_callback_6911_native();return 1;}

/* $698B: post-key progression effect used by callback AF4A. */
static void world_callback_698b_native(void){if(gaw_ram_read8(0xC301u)==0||(gaw_ram_read8(0xC0D3u)&0x80u)==0)return;if(gaw_world_progress_test_and_set())return;gaw_ram_write8(0xDE08u,0xA8u);gaw_world_finalize_transition();}
static int world_run_key_effect_callback(uint16_t target){if(target!=0xAF4Au)return 0;world_try_enter_key_room(0x0314u,5u);world_callback_698b_native();return 1;}

static void world_fixed_item_sequence(uint8_t item){
 gaw_ram_write8(0xC0A3u,item);(void)gaw_world_progress_test_and_set();gaw_world_progress_apply_loaded_patch();gaw_platform_entity_resource_load(item);
 /* $638D/$6398 ends at $229C. Preserve that presentation VBlank even
    though the portable backend owns the actual graphics upload. */
 gaw_wait_frame();
 gaw_hud_update_status_descriptor();gaw_ram_write16le(0xC308u,0x8495u);gaw_ram_write8(0xC30Bu,(uint8_t)((item<0x20u||item==0x2Au)?1u:0u));gaw_ram_write16le(0xC043u,0xA241u);gaw_ram_write8(0xC042u,4u);
 /* $0938 then $229C. */
 gaw_wait_frame();
 gaw_ram_write8(0xDE06u,0x8Cu);for(unsigned i=0;i<180u;++i)gaw_wait_frame();do{gaw_wait_frame();}while((gaw_ram_read8(RAM_INPUT_HELD)&0x3Fu)==0);
 gaw_world_audio_select_native();gaw_ram_write8(0xC301u,0);
 /* Second $6398 before $7219. */
 gaw_wait_frame();gaw_platform_inventory_refresh();gaw_world_finalize_transition();
}
/* $5D59: ten fixed world rewards share one progression/item routine. */
static void world_try_fixed_item(uint16_t pos){
 if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=pos)return;
 if(gaw_world_progress_test_and_set())return;
 gaw_world_progress_restore_for_current_cell();
 uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID),item=0;switch(cell){
  case 0x10:gaw_ram_write8(0xC0E3u,1);item=7;break;case 0x12:gaw_ram_write8(0xC0EAu,1);item=14;break;case 0x1D:gaw_ram_write8(0xC0E1u,2);item=5;break;case 0x57:gaw_ram_write8(0xC0EEu,1);item=18;break;case 0x9B:gaw_ram_write8(0xC0EBu,1);item=15;break;case 0xA2:gaw_ram_write8(0xC0ECu,1);item=16;break;case 0xA9:gaw_ram_write8(0xC0EFu,1);item=19;break;case 0xB6:if(gaw_ram_read8(0xC0E1u)!=0)return;gaw_ram_write8(0xC0E1u,1);item=4;break;case 0xD5:gaw_ram_write8(0xC0F0u,1);item=20;break;case 0xF4:gaw_ram_write8(0xC0EDu,1);item=17;break;default:return;}
 world_fixed_item_sequence(item);
}
static int world_run_fixed_item_callback(uint16_t target){switch(target){case 0xB3DDu:world_try_fixed_item(0x01DCu);return 1;case 0xB3E4u:world_try_fixed_item(0x01D8u);return 1;case 0xB419u:world_try_fixed_item(0x01C4u);return 1;case 0xB4EDu:world_try_fixed_item(0x02E4u);return 1;case 0xB5C4u:world_try_fixed_item(0x0248u);return 1;case 0xB5D7u:world_try_fixed_item(0x01CCu);return 1;case 0xB613u:world_try_fixed_item(0x0358u);return 1;case 0xB64Fu:world_try_fixed_item(0x0264u);return 1;case 0xB6C2u:world_try_fixed_item(0x02C4u);return 1;case 0xB751u:world_try_fixed_item(0x0370u);return 1;default:return 0;}}

static int8_t world_af25_delta(uint8_t c){switch(c){case 0x54:case 0x5D:case 0x9E:case 0xA6:case 0xB5:case 0xBD:case 0xD4:return 10;case 0x43:case 0x7D:case 0xA1:case 0xAC:case 0xB4:case 0xDD:case 0xE2:case 0xE7:return 30;case 0x60:case 0xEE:case 0xF4:return 50;case 0x80:return 100;case 0x90:case 0xA2:case 0xF6:return -10;case 0x5B:case 0xAD:case 0xE4:return -20;case 0x40:case 0x65:case 0x8E:case 0xF1:case 0xF3:return -30;case 0x16:case 0x81:case 0xDB:return -40;default:return 0;}}
/* $6497/AF25: signed resource adjustment selected by C0BB. */
static int world_run_resource_adjust_callback(uint16_t target){if(target!=0xAF25u)return 0;if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read16le(0xC060u)!=0x02DCu)return 1;if(gaw_world_progress_test_and_set())return 1;int d=world_af25_delta(gaw_ram_read8(0xC0BBu));int cur=gaw_ram_read8(0xC0DDu),dst=cur+d;if(dst<0)dst=0;if(dst>255)dst=255;unsigned steps=(unsigned)(dst>cur?dst-cur:cur-dst);gaw_ram_write16le(0xDCE4u,(uint16_t)steps);gaw_platform_world_message(d<0?0x8DF6u:0x8E30u,gaw_ram_read8(0xC0BBu));while(cur!=dst){cur+=(dst>cur)?1:-1;gaw_ram_write8(0xC0DDu,(uint8_t)cur);gaw_ram_write8(0xDE08u,0x95u);gaw_ram_write8(0xC045u,0x83u);hud_update_phase(3u);gaw_ram_write16le(0xDCE4u,(uint16_t)(gaw_ram_read16le(0xDCE4u)-1u));}do{gaw_wait_frame();}while((gaw_ram_read8(RAM_INPUT_HELD)&0x3Fu)==0);gaw_world_finalize_transition();return 1;}

/* $5FC7/B205: one of two permanent capacity rewards selected by the room
   from which the player entered. */
static int world_run_capacity_reward_callback(uint16_t target){if(target!=0xB205u)return 0;if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u||gaw_ram_read16le(0xC060u)!=0x025Cu)return 1;if(gaw_world_progress_test_and_set())return 1;uint8_t from=gaw_ram_read8(0xC0BBu);int magic=(from==0x32u||from==0xC0u||from==0xE5u||from==0xECu);if(magic){world_fixed_item_sequence(0x1Cu);unsigned v=(unsigned)gaw_ram_read8(0xC0DCu)+8u;if(v>0x80u)v=0x80u;gaw_ram_write8(0xC0DCu,(uint8_t)v);gaw_ram_write8(0xC0DBu,(uint8_t)v);}else{world_fixed_item_sequence(0x2Au);unsigned v=(unsigned)gaw_ram_read8(0xC0DAu)+8u;if(v>0x80u)v=0x80u;gaw_ram_write8(0xC0DAu,(uint8_t)v);while(gaw_ram_read8(0xC318u)!=(uint8_t)v){gaw_ram_write8(0xC318u,(uint8_t)(gaw_ram_read8(0xC318u)+1u));gaw_ram_write8(0xDE08u,0x95u);gaw_ram_write8(0xC045u,0x81u);hud_update_phase(1u);}}return 1;}

/* $669D: arm a scripted marker/state when Arthur activates a fixed point. */
static void world_try_script_marker(uint16_t pos,uint8_t value){if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u&&gaw_ram_read16le(0xC060u)==pos){gaw_ram_write8(0xC0A7u,value);gaw_ram_write8(0xC01Du,0x16u);}}
static int world_run_marker_callback(uint16_t target){switch(target){
 case 0xAD41u:world_try_script_marker(0x02D0u,0);world_try_script_marker(0x02E4u,2);gaw_world_callback_65d0_native();return 1;
 case 0xAED1u:world_try_script_marker(0x02DCu,1);gaw_world_callback_65d0_native();return 1;
 case 0xB047u:world_try_script_marker(0x025Cu,0);gaw_world_callback_65d0_native();return 1;
 case 0xB08Fu:world_try_script_marker(0x025Cu,2);gaw_world_callback_65d0_native();return 1;
 case 0xB263u:world_try_script_marker(0x01DCu,3);gaw_world_callback_65d0_native();return 1;
 default:return 0;} }

/* $5CEC: apply the cell's persistent restoration only when its trigger tile
   is empty and the current-layer progress bit has not already been earned. */
static void world_callback_5cec_native(uint8_t cell){if(gaw_world_progress_is_set()||gaw_ram_read8((uint16_t)(0xDC00u+cell))!=0)return;(void)gaw_world_progress_test_and_set();world_callback_5e57_body();}
static int world_run_small_remaining_callback(uint16_t target){switch(target){
 case 0xB42Du:world_callback_5cec_native(0x7Bu);return 1;
 case 0xB459u:world_callback_5cec_native(0x43u);return 1;
 case 0xB574u:world_callback_5cec_native(0x4Au);gaw_world_callback_5ecd_native();return 1;
 case 0xB496u:case 0xB626u:world_temp_gate_begin(0);world_temp_gate_commit();return 1;
 case 0xB758u:world_temp_gate_begin(3);world_temp_gate_commit();return 1;
 case 0xB4FDu:world_temp_gate_begin(3);gaw_world_callback_5ecd_native();return 1;
 case 0xB6FEu:world_temp_gate_begin(2);gaw_world_callback_5ecd_native();return 1;
 case 0xB560u:
  if((gaw_ram_read8(0xC0A6u)&0x77u)==0x14u&&gaw_ram_read16le(0xC060u)==0x0168u&&gaw_ram_read8(0xDC1Bu)!=0x4Du){uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);world_open_gate7(cell);gaw_world_set_tile(0x1Bu,0x4Du);}
  return 1;
 default:return 0;} }

/* Common callback $5D4C, used by 32 cells. */
void gaw_world_callback_5d4c_native(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);world_callback_5e57_body();}
static void gaw_world_callback_5e75_native(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);if(gaw_world_progress_test_and_set())return;if((uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID)==0x13u)world_spawn_type14();gaw_ram_write8(0xDE08u,0xA8u);gaw_world_finalize_transition();}
static void gaw_world_callback_5e9c_native(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);if(world_explicit_progress_test_and_set(3))return;world_callback_5e57_body();gaw_ram_write8(0xDE08u,0xA8u);world_spawn_type14();}
static void gaw_world_callback_5ecd_native(void){if(gaw_ram_read8(0xC0A2u)!=0)return;gaw_ram_write8(0xC0A2u,0x80u);if(!world_explicit_progress_test_and_set(3)){gaw_ram_write8(0xDE08u,0xA8u);world_spawn_type14();}if(gaw_ram_read8(0xC0A8u)==1u){gaw_ram_write8(0xC0A8u,2u);uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);switch(gaw_ram_read8(0xC0A9u)&3u){case 0:case 1:world_open_gate5(cell);break;case 2:world_open_gate6(cell);break;default:world_open_gate7(cell);break;}}}
static int world_run_interactive_callback(uint16_t target);
int gaw_world_native_callback(uint16_t target){
    if(target==0 || target==0xB761u)return 1;
    if(world_run_interactive_callback(target))return 1;
    if(world_run_link_callback(target))return 1;
    if(world_run_progress_gate_callback(target))return 1;
    if(world_run_finalize_callback(target))return 1;
    if(world_run_finalize_gate_callback(target))return 1;
    if(world_run_direct_gate_callback(target))return 1;
    if(world_run_finalize_special_callback(target))return 1;
    if(world_run_composed_callback(target))return 1;
    if(world_run_progress_bits_callback(target))return 1;
    if(world_run_temp_gate_callback(target))return 1;
    if(world_run_room_entry_callback(target))return 1;
    if(world_run_key_room_callback(target))return 1;
    if(world_run_small_remaining_callback(target))return 1;
    if(world_run_marker_callback(target))return 1;
    if(world_run_fixed_item_callback(target))return 1;
    if(world_run_capacity_reward_callback(target))return 1;
    if(world_run_resource_adjust_callback(target))return 1;
    if(world_run_key_effect_callback(target))return 1;
    if(world_run_message_callback(target))return 1;
    if(world_run_special_message_callback(target))return 1;
    if(world_run_context_message_callback(target))return 1;
    if(world_run_key_wave_callback(target))return 1;
    if(target==0x5D4Cu){gaw_world_callback_5d4c_native();return 1;}
    if(target==0x5E75u){gaw_world_callback_5e75_native();return 1;}
    if(target==0x5E9Cu){gaw_world_callback_5e9c_native();return 1;}
    if(target==0x5ECDu){gaw_world_callback_5ecd_native();return 1;}
    if(target==0x654Du){gaw_world_callback_654d_native();return 1;}
    if(target==0x65D0u){gaw_world_callback_65d0_native();return 1;}
    return 0;
}

void gaw_world_run_callback(void) {
    /* $5B5A-$5BAB translated. E is a temporary flag byte in the original. */
    uint8_t e = gaw_ram_read8(0xC30A);
    if (gaw_ram_read8(RAM_INPUT_HELD) & 0x01u) e |= 0x04u;

    uint8_t l = gaw_ram_read8(0xC311);
    uint8_t h = gaw_ram_read8(0xC313);
    uint8_t hd = (uint8_t)(h - 0x28u);
    if (hd < 0xB1u) {
        uint8_t ld = (uint8_t)(l - 0x28u);
        if ((ld & 0x80u) == 0) e |= 0x80u;
    }

    if (((uint8_t)(h | l) & 0x07u) == 0) {
        e |= 0x10u;
        uint16_t old_pos = gaw_ram_read16le(0xC062);
        uint16_t new_pos = gaw_ram_read16le(0xC060);
        gaw_ram_write16le(0xC062, new_pos);
        if (old_pos != new_pos) e |= 0x20u;

        uint8_t old_mode = gaw_ram_read8(0xC064);
        uint8_t new_mode = gaw_ram_read8(0xC30A);
        gaw_ram_write8(0xC064, new_mode);
        if (old_mode != new_mode) e |= 0x40u;
    }
    gaw_ram_write8(0xC0A6, e);

    /* Native $5BB4-$5C93 special interior transition logic. */
    (void)gaw_world_pre_callback_transition();
    uint16_t target = gaw_ram_read16le(RAM_WORLD_CALLBACK);
    /* All 512 table entries resolve to native handlers or the bare RET. */
    (void)gaw_world_native_callback(target);
}


static void gaw_world_audio_select_native(void) {
    static const uint8_t special[11]={0x22,0x2E,0x4C,0x55,0x57,0x94,0x95,0xC7,0xCE,0xF0,0xFE};
    uint8_t mode=gaw_ram_read8(0xC040u),cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID),cmd;
    if(mode==0){cmd=0x82u;for(unsigned i=0;i<11u;++i)if(cell==special[i]){cmd=0x84u;break;}}
    else if(mode==1)cmd=(cell==0xBFu)?0x8Bu:0x87u;
    else {uint8_t f=0;for(unsigned i=0;i<8u;++i)f|=gaw_entity(16u+i)->raw[ENT_FLAGS];if(f&0x40u){gaw_ram_write8(0xC0AEu,1u);cmd=0x86u;}else{gaw_ram_write8(0xC0AEu,0u);cmd=0x83u;}}
    uint8_t old=gaw_ram_read8(0xC065u);gaw_ram_write8(0xC065u,cmd);if(old!=cmd)gaw_ram_write8(0xDE06u,cmd);
}


/* ROM-derived $1780 gameplay-init data. */
static const uint8_t world_entity_types[512u*8u]={
#include "world_entity_types.inc"
};
static const uint8_t map_entity_stats[96u*4u]={
#include "map_entity_stats.inc"
};
static const uint8_t map_entity_resource_spans[96u]={
#include "map_entity_resource_spans.inc"
};

/* $1780-$18E1: construct the eight local C600 map entities, apply the
   per-cell persistence mask and assign compacted graphics slots.  The actual
   resource upload is presentation-only and crosses the platform boundary. */
void gaw_world_spawn_map_entities_native(void){
    memset(gaw_ram_ptr(0xC600u),0,0x300u);
    uint16_t cell=gaw_ram_read16le(RAM_WORLD_CELL_ID);
    if(cell>=512u)cell&=0x01FFu;
    for(unsigned i=0;i<8u;++i){
        GawEntity *e=gaw_entity(16u+i);
        uint8_t type=world_entity_types[(unsigned)cell*8u+i];
        e->raw[ENT_TYPE]=type;
        if(type>=32u){unsigned o=(unsigned)(type-32u)*4u;e->raw[ENT_HP]=map_entity_stats[o];e->raw[ENT_ATTACK]=map_entity_stats[o+1u];e->raw[ENT_DEFENSE]=map_entity_stats[o+2u];e->raw[ENT_FLAGS]=map_entity_stats[o+3u];}
    }

    uint8_t mask=gaw_ram_read8((uint16_t)(0xC200u+(uint8_t)cell));
    for(unsigned i=0;i<8u;++i){uint8_t alive=(uint8_t)(mask&0x80u);mask=(uint8_t)(mask<<1);if(!alive)gaw_entity_clear(gaw_entity(16u+i));}

    uint8_t flags_or=0;for(unsigned i=0;i<8u;++i)flags_or|=gaw_entity(16u+i)->raw[ENT_FLAGS];
    if(flags_or&0x40u){uint8_t item=(uint8_t)gaw_ram_read16le(0xC037u);uint8_t prog=gaw_ram_read8((uint16_t)(0xC0CEu+item));if(prog){memset(gaw_ram_ptr(0xC600u),0,0x180u);if((prog&0x80u)==0)gaw_entity(16)->raw[ENT_TYPE]=15u;}}

    uint8_t active=0;for(unsigned i=0;i<8u;++i)if(gaw_entity(16u+i)->raw[ENT_TYPE])++active;
    gaw_ram_write8(0xC0A2u,active?active:0x80u);

    uint8_t gfx=0;
    for(unsigned i=0;i<8u;++i){
        GawEntity *e=gaw_entity(16u+i);uint8_t type=e->raw[ENT_TYPE];if(type<32u)continue;
        int prior=-1;for(unsigned j=0;j<i;++j)if(gaw_entity(16u+j)->raw[ENT_TYPE]==type){prior=(int)j;break;}
        if(prior>=0){e->raw[ENT_GFX_ID]=gaw_entity(16u+(unsigned)prior)->raw[ENT_GFX_ID];continue;}
        e->raw[ENT_GFX_ID]=gfx;gaw_platform_map_entity_resource_load(type,gfx);
        uint8_t span=map_entity_resource_spans[type-32u];
        /* $032A leaves C031 at the last plane write position.  It is scratch,
           but preserving it makes the high-level init RAM-visible faithful. */
        gaw_ram_write16le(0xC031u,(uint16_t)(0x6003u+(uint16_t)gfx*32u+(uint16_t)span*32u));
        gfx=(uint8_t)(gfx+span);
    }
    gaw_ram_write8(0xC067u,gfx);
}

/* $04E1 portable form used by $1C15. The original mixes the Z80 refresh
   register R into its RAM LFSR; platform entropy is the established portable
   replacement used by the native entity layer as well. */
static uint8_t world_random_byte(void){
    uint16_t hl=gaw_ram_read16le(0xC028u);uint8_t h=(uint8_t)(hl>>8),l=(uint8_t)hl,a=h;
#define WRRCA(v) (uint8_t)(((v)>>1)|((v)<<7))
    a=WRRCA(a);a=WRRCA(a);a^=h;a=WRRCA(a);a^=l;a=WRRCA(a);a=WRRCA(a);a=WRRCA(a);a=WRRCA(a);a^=l;
    uint8_t carry=(uint8_t)(a&1u);hl=(uint16_t)((uint16_t)(hl<<1)+carry);if(hl==0)hl=0x733Cu;gaw_ram_write16le(0xC028u,hl);
#undef WRRCA
    return (uint8_t)(gaw_platform_entropy8()^(uint8_t)hl);
}

/* Interactive scripts $66B5/$66F6/$616F/$6036. Their menus and dialogue
   now write the shared video shadow directly; no instruction execution. */
static uint8_t script_rom(uint16_t a){return gaw_sms_rom_bank_read(1u,a);}
static void script_finish(void){
    gaw_world_expand_metatiles();gaw_hud_rebuild_full();gaw_wait_frame();gaw_ui_upload_name_table();
    for(unsigned i=0;i<16u;++i)gaw_ram_write8((uint16_t)(0xDCB0u+i),gaw_sms_rom_bank_read(0u,(uint16_t)(0x1E20u+i)));
    gaw_hud_update_status_descriptor();
}
static void script_wait_message(void){do{gaw_wait_frame();}while((gaw_ram_read8(RAM_INPUT_PRESSED)&0x3Fu)==0);script_finish();}
static void script_message(uint16_t text){gaw_ui_show_message(text);script_wait_message();}
static void script_currency_step(int delta){
    gaw_ram_write8(0xC0DDu,(uint8_t)(gaw_ram_read8(0xC0DDu)+delta));
    gaw_ram_write8(0xDE08u,0x95);gaw_ram_write8(0xC045u,0x83);
    hud_update_phase(3);gaw_wait_frame();gaw_wait_frame();
}
static int script_pay(uint8_t cost){
    if(gaw_ram_read8(0xC0DDu)<cost){script_message(0x8BCDu);return 0;}
    unsigned n=cost?cost:256u;while(n--)script_currency_step(-1);return 1;
}
static void script_change_cell(uint16_t cell){world_save_local_presence();gaw_ram_write16le(RAM_WORLD_CELL_ID,cell);}
static void script_enter_cell(uint16_t cell){script_change_cell(cell);gaw_ui_wipe_name_table();(void)gaw_world_load_current_cell();}
static int script_gate(uint16_t position){return (gaw_ram_read8(0xC0A6u)&0x77u)==0x14u&&gaw_ram_read16le(0xC060u)==position;}
static uint8_t script_stair_price(void){
    uint16_t p=0x6087u;uint8_t value=0,saved=gaw_ram_read8(0xC0BBu);
    /* $61C3 cost markers update C once, followed by one or more cell IDs. */
    for(;;){uint8_t key=script_rom(p++);if(key==0){value=script_rom(p++);key=script_rom(p++);}if(key==saved)return value;}
}
static int script_stairs(void){
    if((gaw_ram_read8(0xC0A6u)&0x30u)==0x30u&&gaw_ram_read16le(0xC060u)==0x019Cu){
        uint16_t p=0x61A8u;uint8_t saved=gaw_ram_read8(0xC0BBu);
        while(script_rom(p)!=saved)p=(uint16_t)(p+3u);
        p=(uint16_t)(p+9u);
        gaw_ram_write8(0xC0BBu,script_rom(p));gaw_ram_write8(0xC0BDu,script_rom(p+1u));gaw_ram_write8(0xC0BEu,script_rom(p+2u));
        world_return_to_saved_cell();world_explicit_progress_set(gaw_ram_read16le(RAM_WORLD_CELL_ID),0);return 1;
    }
    if(!script_gate(0x025Cu)||gaw_ram_read8(0xDC38u)==1u)return 0;
    gaw_ram_write16le(0xDCE0u,0xDCE4u);gaw_ram_write16le(0xDCE4u,script_stair_price());
    gaw_ui_show_message(0x911Eu);
    if(gaw_ui_yes_no()==0xFFu&&script_pay(script_stair_price())){
        gaw_ram_write16le(0xDC37u,gaw_ram_read16le(0xDC38u));
        gaw_ram_write16le(0xDC47u,gaw_ram_read16le(0xDC48u));
    }
    script_finish();return 1;
}
static int script_game_entry(void){
    if(!script_gate(0x02DCu))return 0;
    gaw_ui_show_message(0xB90Eu);
    if(gaw_ui_yes_no()==0){script_message(0xB930u);return 1;}
    if(!script_pay(10)){script_finish();return 1;}
    script_enter_cell(0x000Bu);gaw_ram_write8(0xC073u,0);gaw_ram_write8(RAM_MAIN_STATE,8);return 1;
}
static void card_refresh(void){gaw_ram_write8(0xDE08u,0x95);script_finish();}
static void card_advance(void){gaw_ram_write8(0xC073u,(uint8_t)(gaw_ram_read8(0xC073u)+1u));}
static int card_apply(uint16_t tile){
    uint16_t table=gaw_ram_read8(0xDC0Cu)==0x38u?0x6801u:0x67F9u;
    uint8_t original=gaw_ram_read8(tile),value=original;
    for(;;){uint8_t from=script_rom(table);if(from&0x80u)break;if(from==original){value=script_rom(table+1u);break;}table=(uint16_t)(table+2u);}
    gaw_ram_write8(tile,value);
    return value!=original;
}
static void card_conversion_pause(void){for(unsigned i=0;i<15u;++i)gaw_wait_frame();card_refresh();}
static void script_card_game(void){
    switch(gaw_ram_read8(0xC073u)){
        case 0:(void)gaw_world_load_current_cell();script_message(0xB94Du);card_advance();break;
        case 1:{
            if((gaw_ram_read8(0xC0A6u)&0x77u)!=0x14u||gaw_ram_read8(0xC061u)!=2u)return;
            uint8_t pos=gaw_ram_read8(0xC060u);unsigned index;
            for(index=0;index<10u;++index)if(pos==script_rom((uint16_t)(0x68ECu+index)))break;
            if(index==10u)return;
            uint16_t slot=(uint16_t)(0xDC00u+script_rom((uint16_t)(0x68F6u+index)));
            if(gaw_ram_read8(slot)!=0x3Au)return;
            for(;;){
                uint8_t kind=script_rom((uint16_t)(0x6776u+(world_random_byte()&0x1Fu)));
                uint16_t pair=(uint16_t)(script_rom((uint16_t)(0x6796u+kind*2u))|
                                        ((uint16_t)script_rom((uint16_t)(0x6797u+kind*2u))<<8));
                uint8_t face=(uint8_t)pair;
                if(face>=0x38u&&gaw_ram_read8(0xDC0Cu)!=0)continue;
                gaw_ram_write8(slot,face);
                if(face>=0x38u){gaw_ram_write16le(0xDC0Cu,pair);card_refresh();script_message(face==0x38u?0xB9D7u:0xBA20u);}
                else{
                    if(gaw_ram_read8(0xDC03u)==0x3Au)gaw_ram_write16le(0xDC03u,pair);
                    else if(gaw_ram_read8(0xDC06u)==0x3Au)gaw_ram_write16le(0xDC06u,pair);
                    else{gaw_ram_write16le(0xDC09u,pair);card_advance();}
                    card_refresh();
                }
                break;
            }
            break;
        }
        case 2:
            if(gaw_ram_read8(0xDC0Cu)!=0){
                for(unsigned i=0;i<10u;++i)if(card_apply((uint16_t)(0xDC33u+i)))card_conversion_pause();
                for(unsigned i=0;i<3u;++i){uint16_t tile=(uint16_t)(0xDC03u+i*3u);(void)card_apply(tile);if(card_apply(tile+1u))card_conversion_pause();}
            }
            card_advance();break;
        case 3:{
            uint8_t sum=0;
            for(unsigned i=0;i<3u;++i)sum=(uint8_t)(sum+script_rom((uint16_t)(0x68C3u+(uint8_t)(gaw_ram_read8((uint16_t)(0xDC03u+i*3u))-0x34u))));
            int current=gaw_ram_read8(0xC0DDu),delta=(int8_t)sum;
            if(delta>0&&current+delta>255)delta=255-current;
            if(delta<0&&current+delta<0)delta=-current;
            unsigned steps=(unsigned)(delta<0?-delta:delta);
            gaw_ram_write16le(0xDCE0u,0xDCE4u);gaw_ram_write16le(0xDCE4u,(uint16_t)steps);
            gaw_ui_show_message(sum&0x80u?0xB982u:0xB95Fu);
            /* Positive $00 follows DJNZ's 256-iteration convention. */
            if((sum&0x80u)==0&&steps==0)steps=256u;
            while(steps--)script_currency_step((sum&0x80u)?-1:1);
            script_wait_message();
            if(gaw_ram_read8(0xC0DDu)>=10u){
                gaw_ui_show_message(0xB9BFu);
                if(gaw_ui_yes_no_card()!=0){
                    (void)gaw_world_load_current_cell();gaw_ui_show_message(0xBA8Eu);(void)script_pay(10);script_wait_message();gaw_ram_write8(0xC073u,1);return;
                }
            }
            script_message(0xB930u);script_enter_cell(0x005Fu);gaw_ram_write8(0xC311u,0x58);gaw_ram_write8(0xC313u,0x88);gaw_ram_write8(RAM_MAIN_STATE,8);break;
        }
        default:break;
    }
}
static int world_run_interactive_callback(uint16_t target){
    switch(target){
        case 0xB19Eu:if(!script_stairs())gaw_world_callback_65d0_native();return 1;
        case 0xB00Au:if(!script_game_entry())gaw_world_callback_65d0_native();return 1;
        case 0xADEEu:script_card_game();return 1;
        default:return 0;
    }
}

static int byte_in_ram(uint16_t base,unsigned n,uint8_t v){for(unsigned i=0;i<n;++i)if(gaw_ram_read8((uint16_t)(base+i))==v)return 1;return 0;}
/* $1C15-$1C90: maintain the recent-cell ring and pre-mark randomly selected
   local encounter slots in C200. */
static void world_seed_random_cells_native(void){
    static const uint8_t interior_excluded[6]={0x1E,0x5E,0x9C,0xB8,0xBE,0xC9};
    unsigned repeats=gaw_ram_read8(0xC0BAu)?5u:3u;
    unsigned recent=gaw_ram_read8(0xC0BAu)?4u:16u;
    uint8_t cell=(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID);
    for(unsigned pass=0;pass<repeats;++pass){
        if(!byte_in_ram(0xDCF0u,recent,cell)){
            memmove(gaw_ram_ptr(0xDCF1u),gaw_ram_ptr(0xDCF0u),recent-1u);
            gaw_ram_write8(0xDCF0u,cell);
        }
        uint8_t r=world_random_byte();
        if(byte_in_ram(0xDCF0u,recent,r))continue;
        if(recent==4u){int excluded=0;for(unsigned i=0;i<sizeof interior_excluded;++i)if(r==interior_excluded[i]){excluded=1;break;}if(excluded)continue;}
        uint16_t a=(uint16_t)(0xC200u+r);if(gaw_ram_read8(a)==0)gaw_ram_write8(a,0xFFu);
    }
}

void gaw_state_gameplay_init(void) {
    /* $24C5-$24DC: exact clear ranges, including the first byte. */
    memset(gaw_ram_ptr(0xC090), 0, 0x20u);
    memset(gaw_ram_ptr(0xC4B0), 0, 0x150u);

    world_seed_random_cells_native();
    gaw_world_spawn_map_entities_native();
    gaw_player_init_from_world();
    gaw_world_select_callback();
    gaw_world_audio_select_native();
    gaw_ram_write8(RAM_MAIN_STATE, 0x0C);
}




static void queue_vram_copy(uint16_t dst,uint16_t src,uint8_t len){
    uint16_t q=gaw_ram_read16le(0xC034);
    if(q<GAW_RAM_BASE||q>0xDFF9u)return;
    gaw_ram_write8(q,1);q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,0xFF);q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,(uint8_t)dst);q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,(uint8_t)(dst>>8));q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,(uint8_t)src);q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,(uint8_t)(src>>8));q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write8(q,len);q=(uint16_t)((q&0xFF00u)|((q+1u)&0xFFu));
    gaw_ram_write16le(0xC034,q);
}
static void animate_mode0_bank5(void){
    uint8_t f=gaw_ram_read8(RAM_FRAME_COUNTER);
    if((f&7u)!=0)return;
    unsigned phase=(unsigned)((f>>3)&3u);
    for(unsigned i=0;i<4u;++i)gaw_ram_write8((uint16_t)(0xDCACu+i),gaw_sms_rom_bank_read(5u,(uint16_t)(0xBDB7u+phase+i)));
}
static void animate_mode2_bank5(void){
    uint8_t f=gaw_ram_read8(RAM_FRAME_COUNTER);
    if(gaw_ram_read8(0xC072)!=0 && gaw_ram_read8(0xC0AD)==0)return;
    uint16_t src;
    if(gaw_ram_read8(0xC0AE)!=0) src=0xBDF0u;
    else { if((f&3u)!=0)return; src=(uint16_t)(0xBDF3u+3u*((f>>2)&3u)); }
    for(unsigned i=0;i<3u;++i)gaw_ram_write8((uint16_t)(0xDCADu+i),gaw_sms_rom_bank_read(5u,(uint16_t)(src+i)));
}

/* $699C-$6AE1. Cursor restoration is native; full-screen effects 1/2
   still use their original instruction stream. Both receive the correct IX. */
void gaw_world_animate_frame(void){
    static const uint16_t effect_states[5]={0,0x6AFBu,0x6C2Eu,0x6D2Cu,0x6D40u};
    for(unsigned slot=0;slot<2u;++slot){
        uint16_t address=(uint16_t)(0xC090u+slot*8u);
        uint8_t state=gaw_ram_read8(address);
        if(!gaw_effect_native_step(address)&&state<5u)
            gaw_sms_compat_indexed_call(1,effect_states[state],address);
    }
    uint8_t mode=gaw_ram_read8(0xC040), f=gaw_ram_read8(RAM_FRAME_COUNTER);
    if(mode==0){
        animate_mode0_bank5();
        if((f&7u)!=0)return;
        uint16_t dst=(uint16_t)(0x9000u+((uint16_t)(f&0x18u)<<4));
        uint16_t src=(uint16_t)(0x4000u+(uint16_t)gaw_sms_rom_bank_read(0,0x253Au)*32u);
        queue_vram_copy(dst,src,4);return;
    }
    if(mode==1){
        uint8_t cell=(uint8_t)(gaw_ram_read8(0xC0AA)+5u);if(cell>=0xA0u)cell=0;gaw_ram_write8(0xC0AA,cell);
        for(unsigned i=0;i<5u;++i){uint8_t c=(uint8_t)(cell+i),tile=gaw_ram_read8((uint16_t)(0xDC00u+c));if(tile>=0x24u&&tile<0x30u)gaw_world_set_tile(c,(uint8_t)(tile^1u));}
        if(f&1u)return;
        uint16_t dst=(f&2u)?0x9080u:0x9000u;
        uint8_t tile=gaw_ram_read8(0xC9E0);uint16_t src=(uint16_t)(0x4000u+(uint16_t)tile*32u);
        queue_vram_copy(dst,src,4);return;
    }
    animate_mode2_bank5();
    if((f&7u)==0){
        static const uint16_t dsts[4]={0x9000u,0x90C0u,0x9180u,0x90C0u};
        uint8_t tile=gaw_ram_read8(0xC930);uint16_t src=(uint16_t)(0x4000u+(uint16_t)tile*32u);
        queue_vram_copy(dsts[(f>>3)&3u],src,6);
    }
    uint8_t phase=gaw_ram_read8(0xC0AB);
    if((phase&1u)==0){
        static const uint8_t seq[9]={0x41,0x4E,0x4F,0x50,0x50,0x4F,0x4E,0x41,0x41};
        unsigned k=phase>>1;uint8_t from=seq[k],to=seq[k+1u],cell=gaw_ram_read8(0xC0AA),changed=0;
        for(unsigned i=0;i<4u;++i){uint8_t c=(uint8_t)(cell+i);if(gaw_ram_read8((uint16_t)(0xDC00u+c))==from){++changed;gaw_world_set_tile(c,to);}}
        if(changed){gaw_ram_write8(0xC0AB,(uint8_t)((phase+1u)&15u));return;}
    }else{
        phase=(uint8_t)((phase+1u)&15u);gaw_ram_write8(0xC0AB,phase);if(phase!=0)return;
    }
    uint8_t cell=(uint8_t)(gaw_ram_read8(0xC0AA)+4u);if(cell>=0x90u)cell=0x20u;gaw_ram_write8(0xC0AA,cell);
}

static uint8_t render_rom12(uint16_t a){return gaw_sms_rom_bank_read(12u,a);}

/* $09EE: append one entity's sprite pieces to the SMS-format staging buffers
   at DD40 (X) and DD80 (Y/tile). */
static void render_entity_sms(GawEntity *e){
    uint16_t p=(uint16_t)(((uint16_t)e->raw[0x09]<<8)|e->raw[0x08]);
    p=(uint16_t)(p+(uint16_t)e->raw[0x0A]*2u);
    uint16_t frame=(uint16_t)(render_rom12(p)|((uint16_t)render_rom12((uint16_t)(p+1u))<<8));
    frame=(uint16_t)(frame+(uint16_t)e->raw[0x0B]*2u);
    uint16_t d=(uint16_t)(render_rom12(frame)|((uint16_t)render_rom12((uint16_t)(frame+1u))<<8));
    uint8_t header=render_rom12(d++), count=(uint8_t)(header&0x7Fu);
    e->raw[0x1B]=render_rom12(d++); e->raw[0x1C]=render_rom12(d++);
    uint16_t xp=gaw_ram_read16le(0xC024), yp=gaw_ram_read16le(0xC026);
    uint8_t xcur=e->raw[0x11];
    for(unsigned i=0;i<count;++i){xcur=(uint8_t)(xcur+render_rom12(d++));gaw_ram_write8(xp++,xcur);}
    uint8_t ycur=e->raw[0x13];
    for(unsigned i=0;i<count;++i){
        ycur=(uint8_t)(ycur+render_rom12(d++));gaw_ram_write8(yp++,ycur);
        uint8_t tile=render_rom12(d++);
        if((header&0x80u)==0)tile=(uint8_t)(tile+e->raw[0x02]);
        gaw_ram_write8(yp++,tile);
    }
    gaw_ram_write16le(0xC024,xp);gaw_ram_write16le(0xC026,yp);
}

/* $0940-$0A60: build the sprite staging list.  With many sprites (or after
   SMS overflow) the original rotates slot order every frame; with a small
   set it sorts active sprites by X before emitting them. */
void gaw_render_build_sms_sat(void){
    gaw_ram_write16le(0xC024,0xDD40u);gaw_ram_write16le(0xC026,0xDD80u);
    uint8_t frame=gaw_ram_read8(RAM_FRAME_COUNTER), active=gaw_ram_read8(RAM_ACTIVE_ENTITY_COUNT);
    if(active>=8u || (gaw_ram_read8(RAM_VDP_STATUS)&0x40u)!=0){
        for(unsigned n=0;n<32u;++n){
            unsigned slot;
            switch(frame&3u){
                case 0: slot=n; break;
                case 1: slot=n<16u?n+16u:31u-n; break;
                case 2: slot=n<16u?15u-n:47u-n; break;
                default: slot=n<16u?31u-n:n-16u; break;
            }
            GawEntity *e=gaw_entity(slot);
            if(e && e->raw[ENT_TYPE]!=0 && (e->raw[ENT_FLAGS]&1u))render_entity_sms(e);
        }
    }else{
        uint8_t slots[32], xs[32], count=0;
        for(int slot=31;slot>=0;--slot){
            GawEntity *e=gaw_entity((unsigned)slot);
            if(!e || (e->raw[ENT_FLAGS]&1u)==0)continue;
            uint8_t x=e->raw[0x11], pos=0;
            while(pos<count && x<xs[pos])++pos;
            for(unsigned j=count;j>pos;--j){xs[j]=xs[j-1u];slots[j]=slots[j-1u];}
            xs[pos]=x;slots[pos]=(uint8_t)slot;++count;
        }
        for(unsigned i=0;i<count;++i){gaw_ram_write8((uint16_t)(0xD100u+i),slots[i]);gaw_ram_write8((uint16_t)(0xD140u+i),xs[i]);}
        gaw_ram_write8((uint16_t)(0xD100u+count),0xFF);
        for(unsigned i=0;i<count;++i)render_entity_sms(gaw_entity(slots[i]));
    }
    gaw_ram_write8(gaw_ram_read16le(0xC024),0xD0);
}

/* $1E99-$1F53: one quarter of the HUD is rebuilt each frame.  Keeping this
   in high-level C removes a per-frame trip through the instruction bridge. */
static void hud_update_phase(uint8_t phase) {
    switch (phase & 3u) {
        case 0: {
            static const uint8_t desc[18] = {
                0x85,0x82, 0x83,0x8E, 0x87,0x86, 0x89,0x8A, 0x82,0x44,
                0x88,0x4C, 0x86,0x06, 0x84,0x0A, 0x8A,0x48
            };
            for (unsigned i=0;i<9u;++i) {
                if ((gaw_ram_read8((uint16_t)(0xC0CFu+i)) & 0x80u) == 0) continue;
                uint16_t dst=(uint16_t)(0xDB00u+desc[i*2u+1u]);
                gaw_ram_write8(dst,desc[i*2u]);
                gaw_ram_write8((uint16_t)(dst+1u),0x59);
            }
            break;
        }
        case 1: {
            uint16_t dst=0xDB5Eu;
            uint8_t hp=gaw_ram_read8(0xC318);
            unsigned slots=(unsigned)(gaw_ram_read8(0xC0DA)>>3);
            for (unsigned i=0;i<slots;++i) {
                uint8_t tile;
                if (hp >= 8u) { hp=(uint8_t)(hp-8u); tile=0x8B; }
                else {
                    /* $1F0E-$1F16: 0..7 HP maps to $8F,$8F,$8E,$8E,$8D,$8D,$8C,$8C. */
                    tile=(uint8_t)(0x8Fu-(hp>>1));
                    hp=0;
                }
                gaw_ram_write8(dst++,tile); gaw_ram_write8(dst++,0x19);
                if (tile != 0x8B) {
                    while (++i<slots) { gaw_ram_write8(dst++,0x8F); gaw_ram_write8(dst++,0x19); }
                    break;
                }
            }
            break;
        }
        case 2: {
            uint16_t dst=0xDBDEu;
            uint8_t value=gaw_ram_read8(0xC0DB);
            unsigned slots=(unsigned)(gaw_ram_read8(0xC0DC)>>3);
            for (unsigned i=0;i<slots;++i) {
                uint8_t tile;
                if (value >= 8u) { value=(uint8_t)(value-8u); tile=0x90; }
                else { tile=0x91; value=0; }
                gaw_ram_write8(dst++,tile); gaw_ram_write8(dst++,0x19);
                if (tile==0x91) {
                    while (++i<slots) { gaw_ram_write8(dst++,0x91); gaw_ram_write8(dst++,0x19); }
                    break;
                }
            }
            break;
        }
        default: {
            uint8_t value=gaw_ram_read8(0xC0DD);
            uint8_t hundreds=(uint8_t)(value/100u); value=(uint8_t)(value%100u);
            uint8_t tens=(uint8_t)(value/10u), ones=(uint8_t)(value%10u);
            const uint8_t d[3]={(uint8_t)(0xF0u+hundreds),(uint8_t)(0xF0u+tens),(uint8_t)(0xF0u+ones)};
            uint16_t dst=0xDBD0u;
            for(unsigned i=0;i<3u;++i){gaw_ram_write8(dst++,d[i]);gaw_ram_write8(dst++,0x18);}
            break;
        }
    }
}

void gaw_hud_update_quarter_frame(void) {
    uint8_t frame=gaw_ram_read8(RAM_FRAME_COUNTER);
    gaw_ram_write8(0xC045,(uint8_t)(frame|0x80u));
    hud_update_phase(frame);
}

void gaw_hud_rebuild_full(void) {
    uint16_t src=0xA6ABu;
    for(unsigned plane=0;plane<2u;++plane){uint16_t dst=(uint16_t)(0xDB00u+plane);for(;;){uint8_t cmd=gaw_sms_rom_bank_read(4u,src++);if(cmd==0)break;if(cmd&0x80u){unsigned n=cmd&0x7Fu;if(n==0)n=256u;while(n--){gaw_ram_write8(dst,gaw_sms_rom_bank_read(4u,src++));dst=(uint16_t)(dst+2u);}}else{unsigned n=cmd;uint8_t v=gaw_sms_rom_bank_read(4u,src++);while(n--){gaw_ram_write8(dst,v);dst=(uint16_t)(dst+2u);}}}}
    for(unsigned i=0;i<128u;++i){uint16_t q=(uint16_t)(0xDB00u+i*2u);gaw_ram_write8(q,(uint8_t)(gaw_ram_read8(q)+0xD0u));gaw_ram_write8((uint16_t)(q+1u),(uint8_t)(gaw_ram_read8((uint16_t)(q+1u))|0x18u));}
    static const uint8_t block[8]={0xEC,0x18,0xED,0x18,0xEE,0x18,0xEF,0x18};for(unsigned row=0;row<2u;++row)memcpy(gaw_ram_ptr((uint16_t)(0xDB58u+row*0x40u)),block+row*4u,4u);
    hud_update_phase(0);hud_update_phase(3);hud_update_phase(2);hud_update_phase(1);
    for(unsigned i=0;i<128u;++i){uint16_t q=(uint16_t)(0xDB01u+i*2u);gaw_ram_write8(q,(uint8_t)(gaw_ram_read8(q)|0x40u));}
}


/* $1DF6-$1E1F: small animated HUD descriptor update. */
void gaw_hud_update_status_descriptor(void) {
    static const uint16_t table[3]={0x002Au,0x3038u,0x132Bu};
    uint8_t idx=gaw_ram_read8(0xC0F1);
    uint16_t v=table[idx<3u?idx:0u];
    gaw_ram_write16le(0xDCB6,v);
    if (gaw_ram_read8(0xC0BF)!=0) {
        uint8_t f=gaw_ram_read8(RAM_FRAME_COUNTER);
        if ((f&0x02u)==0) gaw_ram_write16le(0xDCB6,0x0116u);
    }
    gaw_ram_write8(0xDCBF,(gaw_ram_read8(RAM_FRAME_COUNTER)&2u)?2u:1u);
}

void gaw_state_gameplay(void) {
    gaw_wait_frame();
    gaw_entities_update_all();
    gaw_render_build_sms_sat();
    gaw_hud_update_quarter_frame();
    gaw_world_run_callback();
    gaw_world_animate_frame();
    gaw_hud_update_status_descriptor();
    (void)gaw_world_check_boundary_transition();

    /* $250B onward. C318 is entity slot 0 + $18 (health-like field). */
    if (gaw_ram_read8(0xC318) == 0) return;
    if (gaw_ram_read8(RAM_MAIN_STATE) != 0x0C) return;

    if (gaw_ram_read8(RAM_INPUT_PRESSED) & 0x10u) {
        gaw_ram_write8(RAM_MAIN_STATE, 0x10);
    } else if (gaw_ram_read8(RAM_PAUSE_PRESSED) != 0) {
        gaw_ram_write8(RAM_MAIN_STATE, 0x02);
    }
}

void gaw_dispatch_state_once(void) {
    uint8_t state = gaw_ram_read8(RAM_MAIN_STATE);
    if ((state & 1u) || state > 0x16u) return;

    switch (state) {
        case 0x0A: gaw_state_gameplay_init(); break;
        case 0x0C: gaw_state_gameplay(); break;
        default:
            {
                uint16_t target = gaw_main_state_targets[state >> 1];
                uint8_t bank = (target < 0x4000u) ? 0u : 1u;
                gaw_recompiled_call(bank, target);
            }
            break;
    }
}
