#include "include/gaw_video.h"

/* Private cartridge data; independent of the ROM-free video shadow. */
static const uint8_t rom[0x40000]={
#include "original_rom.inc"
};
uint8_t gaw_sms_rom_bank_read(uint8_t bank,uint16_t cpu_addr){
    return *gaw_sms_rom_bank_data(bank,cpu_addr);
}
const uint8_t *gaw_sms_rom_bank_data(uint8_t bank,uint16_t cpu_addr){
    return &rom[(uint32_t)(bank&15u)*0x4000u+(cpu_addr&0x3FFFu)];
}
