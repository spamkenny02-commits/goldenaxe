#include "include/gaw_core.h"
#include "include/gaw_platform.h"
#include "include/gaw_ram.h"
#include "include/gaw_sms_compat.h"

/* $0404-$0443. The overlapping LDIR clears $8010 through $9FFE,
   inclusive, preserving the reserved first 16 bytes and the last byte.
   On a bad signature the original leaves C036 unchanged. */
void gaw_save_initialize_native(void) {
    uint16_t page=(gaw_ram_read8(0xDFFCu)&4u)?0x4000u:0u;
    unsigned i;
    for(i=0;i<26u;++i) {
        if(gaw_platform_sram_read((uint16_t)(page+0x10u+i))!=
           gaw_sms_rom_bank_read(0u,(uint16_t)(0x03EAu+i))) break;
    }
    if(i==26u) {
        gaw_ram_write8(0xC036u,gaw_platform_sram_read((uint16_t)(page+0x30u)));
        return;
    }
    for(i=0x10u;i<0x1FFFu;++i)
        gaw_platform_sram_write((uint16_t)(page+i),0);
    for(i=0;i<26u;++i)
        gaw_platform_sram_write((uint16_t)(page+0x10u+i),
                               gaw_sms_rom_bank_read(0u,(uint16_t)(0x03EAu+i)));
    gaw_platform_sram_write((uint16_t)(page+0x30u),0);
}

/* $03C0-$03DE. The final RST $28 sends DE=$C010 verbatim, selecting
   CRAM index $10 (command 3), not VRAM. Both backends share this shadow. */
void gaw_video_initialize_native(void) {
    for(unsigned i=0;i<11u;++i) {
        uint8_t value=gaw_sms_rom_bank_read(0u,(uint16_t)(0x03DFu+i));
        gaw_ram_write8((uint16_t)(0xC010u+i),value);
        gaw_sms_vdp_control_write(value);
        gaw_sms_vdp_control_write((uint8_t)(0x80u+i));
    }
    gaw_sms_vdp_control_write(0x10u);
    gaw_sms_vdp_control_write(0xC0u);
    gaw_sms_vdp_data_write(0);
}
