#ifndef GAW_EFFECTS_H
#define GAW_EFFECTS_H
#include <stdint.h>
/* Runs the four original effect states; returns zero for invalid state values. */
int gaw_effect_native_step(uint16_t state_address);
#endif
