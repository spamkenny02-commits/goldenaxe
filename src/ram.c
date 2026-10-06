#include <string.h>
#include "include/gaw_ram.h"

uint8_t gaw_ram[GAW_RAM_SIZE];

void gaw_ram_reset_like_z80(void) {
    /* $009E..$00A9: C010 is zeroed, then LDIR copies it through DFEF.
       C000..C00F and DFF0..DFFF are intentionally not part of this clear. */
    memset(gaw_ram_ptr(0xC010), 0, 0x1FE0u);
}
