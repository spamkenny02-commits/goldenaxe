#ifndef GAW_CORE_H
#define GAW_CORE_H
#include <stdbool.h>
#include <stdint.h>

void gaw_reset(void);
void gaw_save_initialize_native(void); /* $0404 */
void gaw_video_initialize_native(void); /* $03C0 */
void gaw_dispatch_state_once(void);
bool gaw_main_state_is_native(uint8_t state); /* shared dispatcher registration */
void gaw_state_enter_gameplay(void); /* original $24B6, state value $08 */
void gaw_state_gameplay_init(void); /* original $24C5, state value $0A */
void gaw_world_spawn_map_entities_native(void); /* original $1780 */
void gaw_state_gameplay(void);      /* original $24F3, state value $0C */
void gaw_state_inventory(void); /* $70F2, state $10 */
void gaw_wait_frame(void);          /* portable form of $0B95 */
void gaw_nmi_pause(void);           /* original NMI behavior at $0066 */
void gaw_vblank_tick(uint8_t held_bits); /* native video/input/frame IRQ portion */
void gaw_world_select_callback(void);    /* core of $5B20 */
void gaw_world_run_callback(void);
void gaw_world_callback_5d4c_native(void);
int gaw_world_native_callback(uint16_t target);       /* callback portion of $5B5A */
void gaw_world_animate_frame(void);       /* $699C */
void gaw_render_build_sms_sat(void);      /* $0940 */
void gaw_hud_update_quarter_frame(void); /* $1E99 */
void gaw_hud_rebuild_full(void); /* $1E4E */
void gaw_world_rebuild_display_native(void); /* $1DE2, no progress reapplication */
void gaw_hud_update_status_descriptor(void); /* $1DF6 */
void gaw_hud_initialize_status_descriptor(void); /* $1DEB */

#endif
