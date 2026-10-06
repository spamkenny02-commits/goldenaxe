#ifndef GAW_MENU_H
#define GAW_MENU_H
#include <stdint.h>
void gaw_state_name_entry(void); /* $1101, state $12 */
void gaw_state_title_intro(void); /* $146D, state $00 */
void gaw_title_choose(void); /* $14ED */
void gaw_menu_reset_sound(void); /* $0B48 */
void gaw_menu_load_name_resources(void); /* $1260 */
void gaw_state_ending(void); /* $6EBE, state $0E */
void gaw_name_cursor(void); /* $12C1 */
void gaw_name_input(void); /* $11BA */
void gaw_menu_message(uint16_t resource); /* $779B */
void gaw_menu_wait_input(uint8_t mask); /* $7447 */
void gaw_state_services(void); /* $7390, state $16 */
uint8_t gaw_menu_choose(uint8_t limit); /* $7716 */
void gaw_menu_cursor(void); /* $7744 */
void gaw_services_draw_portrait(void); /* $77B7 */
void gaw_services_draw_saves(void); /* $782C */
void gaw_services_draw_save_names(void); /* $7842 */
void gaw_services_draw_shop(void); /* $78CE */
#endif
