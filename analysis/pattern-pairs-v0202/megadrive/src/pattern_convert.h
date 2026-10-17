#ifndef GAW_PATTERN_CONVERT_H
#define GAW_PATTERN_CONVERT_H
#include <types.h>
/* Source must be even-aligned on68000; one row is four SMS plane bytes.
 * Output is one MD packed-pixel word per row, high nibble leftmost. */
void pattern_convert(const u8 *source,u32 *destination,u16 rows);
#endif
