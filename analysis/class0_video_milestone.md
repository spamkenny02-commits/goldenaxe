# Physical class-0 video transfers and audio output

The experimental source-clock loader now has a physical Mega Drive publisher.
The playable cartridge remains byte-identical to v0203; this loader is still
outside the game loop.

The publisher transfers 193 base-pattern tiles derived directly from the SMS
ROM, translates the complete 768-word name table, and uploads 32 palette words.
A 128 KiB attribute table accepts native-endian words without byte swapping;
the 68000 loop handles four words per DBRA. The atlas needs no runtime planar
conversion. This trades ROM space for CPU time, rather than using captured
screens or per-room test results as assets.

The atlas and palette use DMA. The short name-table rows use direct CPU port
bursts, avoiding repeated generic DMA setup. While the display is disabled,
the publisher temporarily uses H40 for DMA bandwidth, then restores H32.
The tested BG_A layout is 64x32 with the visible 32x24 image at row two.
Other tile slots and the backdrop remain the caller's responsibility.

The source IRQ adapter also avoids copying all 336 RAM bytes for audio-only
interrupts: it stages only C030 and commits it after successful audio work.
Full interrupts retain their existing staging. Audio-only output stages are
zeroed directly instead of copied from a temporary array. Source T/M1 and RAM
results remain unchanged, including rejected operations.

## Checks

- Host: all 65536 attribute words, 65536 map words, 256 upper-palette inputs
  and 12352 atlas pixels agree with independent bit/plane decoding.
- Compiled 68000 PAL/NTSC: all 65536 words, tail lengths 0-7, output guards
  and null/display-enabled upload rejection pass.
- 24 source-checked loading contexts physically publish 18432 map words,
  296448 atlas pixels and 768 CRAM words. Two adjacent guard tiles per case
  remain intact; H32 and the64x32 plane configuration are verified afterward.
- All sixteen source checkpoints for the24 complete loading contexts remain
  conformant on host and 68000. The56 three-class prefixes and retained
  wait/raster/latched-IRQ vectors pass again. Eleven adapter boundary cases
  include audio-only failure rollback and timer values 0,2 and255.

## Complete-chain measurements

Read-only PC markers include model computation, actual PSG writes, conversion
and physical transfers. Marker overhead and PSG counters are included.

| Physical region | First physical prototype, frames | Current physical path, frames | Source duration, frames |
| --- | ---: | ---: | ---: |
| NTSC | 22.7396-23.8882 | 21.5641-22.7044 | 22.7104 |
| PAL | 18.1199-18.9810 | 17.2006-18.0602 | 19.5707 |

The smallest measured NTSC remainder is only **1.64 scanlines**, versus
472.86 in PAL. This is too thin to call the renderer generally ready.
The measurements cover twelve matching-region contexts each, not all rooms,
stats, inputs or real hardware. Raw data correctness and total elapsed time
do not establish publication at the correct source deadlines.

PSG writes reach the actual emulated port but are not deadline-paced yet.
The display stays disabled; hero/actor/font uploads, backdrop setup, sprites,
screen enable/fades and global source-entry phase propagation remain outside
this test. Palette words use the existing port DAC mapping [0,3,5,7]; exact
source RGB/analogue output is not claimed. There is no complete-frame or
whole-game fidelity claim.

## Reproduction

```
python tools/validate_class0_video.py --68k
python tools/validate_native_irq_context_boundaries.py
python tools/validate_native_source_wait_unit.py
python tools/validate_native_room_finish.py --planned
python tools/validate_native_room_finish_68k.py --planned
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video
```

Retained fixtures are required. Build regenerates the ROM-derived video assets.
Proof snapshots are in `class0-video-v0203`; the slower first prototype and its
exact assets are preserved in `class0-video-first-pass`. Full emulator state
dumps remain disabled.
