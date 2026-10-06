#ifndef GAW_EFFECTS_H
#define GAW_EFFECTS_H
#include <stdint.h>
/* Returns zero for effects whose full animation is still bridged. */
int gaw_effect_native_step(uint16_t state_address);
#endif
