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
void gaw_ui_fade_in(void); /* $0AA4 */
void gaw_ui_fade_out(void); /* $0B12 */
void gaw_ui_fade_grayscale(void); /* $263E */
void gaw_ui_load_choice_font(uint16_t resource); /* $0C68 */
void gaw_ui_reveal_world(void); /* $1FA7 */
void gaw_ui_status_box(void); /* $6398 */
void gaw_ui_status_font(void); /* $638D font portion */
void gaw_ui_fixed_text(uint16_t source,uint16_t destination); /* $0812 */
void gaw_ui_inventory_text(uint16_t source,uint16_t destination); /* $0818 */
void gaw_ui_decimal(uint8_t value,uint16_t destination); /* $085B */
void gaw_ui_load_font(uint8_t characters,uint16_t destination); /* $0C36 */
void gaw_ui_clear_playfield(void); /* $20DA */
#endif
