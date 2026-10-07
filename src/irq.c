#include "include/gaw_platform.h"
#include "include/gaw_audio.h"
#include "include/gaw_core.h"
#include "include/gaw_presentation.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"

static void edge_update(uint16_t held, uint16_t pressed, uint8_t now) {
    uint8_t old = gaw_ram_read8(held);
    gaw_ram_write8(held, now);
    gaw_ram_write8(pressed, (uint8_t)(now & (now ^ old)));
}

static void timer_tick(void) {
    uint8_t timer = gaw_ram_read8(RAM_TIMER_C030);
    if (timer) gaw_ram_write8(RAM_TIMER_C030, (uint8_t)(timer - 1u));
}

/* $025E dispatches one of three line handlers. Their busy waits become
   scanline scheduling in the platform backend, not CPU instruction delays. */
static void line_irq(void) {
    switch (gaw_ram_read16le(0xC02Cu)) {
        case 0x0263: {
            uint8_t mode = gaw_ram_read8(0xC010u) & 0xEFu;
            gaw_ram_write8(0xC010u, mode);
            gaw_platform_video_command((uint16_t)(0x8000u|mode));
            break;
        }
        case 0x0275:
            gaw_platform_video_command(0x8800u);
            break;
        case 0x0280:
            gaw_platform_video_command(0xC010u);
            gaw_sms_vdp_data_write(0);
            break;
    }
}

/* $0038/$0137. An asynchronous VBlank updates audio and the timer only;
   input edges and the game frame counter belong to the synchronous barrier. */
void gaw_irq_service(uint8_t held_bits) {
    uint8_t status = gaw_video_status_read();
    if (!(status & 0x80u)) {
        line_irq();
        return;
    }
    gaw_ram_write8(RAM_VDP_STATUS, status);
    if (!gaw_ram_read8(RAM_VBLANK_WAIT_FLAG)) {
        gaw_audio_tick();
        timer_tick();
        return;
    }
    gaw_video_present_vblank();
    gaw_audio_tick();
    uint8_t pause = 0;
    uint8_t counter = gaw_ram_read8(RAM_PAUSE_NMI_COUNTER);
    if (counter) {
        gaw_ram_write8(RAM_PAUSE_NMI_COUNTER, (uint8_t)(counter - 1u));
        pause = 1;
    }
    edge_update(RAM_PAUSE_HELD, RAM_PAUSE_PRESSED, pause);
    edge_update(RAM_INPUT_HELD, RAM_INPUT_PRESSED, held_bits & 0x3Fu);
    timer_tick();
    gaw_ram_write8(RAM_FRAME_COUNTER,
                  (uint8_t)(gaw_ram_read8(RAM_FRAME_COUNTER) + 1u));
    gaw_ram_write8(RAM_VBLANK_WAIT_FLAG, 0);
}

void gaw_vblank_tick(uint8_t held_bits) {
    gaw_video_vblank_pending();
    gaw_irq_service(held_bits);
}
