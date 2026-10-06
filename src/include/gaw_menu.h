#ifndef GAW_MENU_H
#define GAW_MENU_H
#include <stdint.h>
void gaw_state_name_entry(void); /* $1101, state $12 */
void gaw_name_cursor(void); /* $12C1 */
void gaw_name_input(void); /* $11BA */
void gaw_menu_message(uint16_t resource); /* $779B */
void gaw_menu_wait_input(uint8_t mask); /* $7447 */
#endif
