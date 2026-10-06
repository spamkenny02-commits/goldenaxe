#ifndef GAW_AUDIO_H
#define GAW_AUDIO_H
#include <stdint.h>
void gaw_audio_tick(void); /* bank 6 $8000, one driver update */
uint32_t gaw_audio_faults(void); /* malformed/reserved stream commands */
void gaw_audio_reset_diagnostics(void);
#endif
