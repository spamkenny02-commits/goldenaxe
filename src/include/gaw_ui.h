#ifndef GAW_UI_H
#define GAW_UI_H
#include <stdint.h>
void gaw_ui_box(uint16_t dst,uint8_t width,uint8_t height); /* $0877 */
void gaw_ui_upload_name_table(void); /* $0914, no VBlank */
uint8_t gaw_ui_yes_no(void); /* $60BC, $FF=yes, $00=no */
uint8_t gaw_ui_yes_no_fixed(void); /* $6093 */
uint8_t gaw_ui_yes_no_card(void); /* $60B1 */
void gaw_ui_show_message(uint16_t resource); /* $050C */
void gaw_ui_wipe_name_table(void); /* $1F78, twenty VBlank passes */
void gaw_ui_display_reset(void); /* $0B24 */
#endif
