#ifndef GAW_SOURCE_PATTERN_H
#define GAW_SOURCE_PATTERN_H
#include "source_clock.h"

/* 032A: four interleaved pattern planes. Valid source streams only, as in
 * the original loader. address is the SMS VDP destination (for carry costs).
 * Optional work excludes IRQs/contention; it does not advance a live clock. */
const u8 *source_pattern_decode(const u8 *source,u8 *destination,u16 address,
                                SourceClockWork *work);
#endif
