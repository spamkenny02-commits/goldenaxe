#ifndef GAW_HOST_H
#define GAW_HOST_H
#include <stdint.h>
void gaw_host_set_pad(uint8_t held_bits);
void gaw_host_set_entropy(uint8_t value);
void gaw_host_pulse_pad(unsigned start_frame,unsigned duration,uint8_t bits);
unsigned gaw_host_frame_count(void);
void gaw_host_queue_pad(unsigned frame,uint8_t bits);
void gaw_host_set_entropy_sequence(const uint8_t *values,unsigned count);
void gaw_host_queue_pause(unsigned frame);
/* Called after the frame tick; platform initialization clears the observer. */
void gaw_host_set_frame_observer(void (*observer)(void));
#endif
