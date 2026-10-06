#ifndef GAW_PRESENTATION_H
#define GAW_PRESENTATION_H
#include <stdint.h>
void gaw_video_flush_queue(uint8_t bank); /* $0293 */
void gaw_video_present_vblank(void); /* video portion $013E-$0199 */
#endif
