# V43 — Reduce native sprite-status and clipping work

## Changes

The collision bitmap is now declared as aligned 32-bit words, cleared with eight
word stores per touched scanline instead of a 32-byte memset loop on the 68000.
The collision path accesses these words through character bytes, which is legal
C aliasing and does not depend on host endianness. The three-byte opacity merge
uses constant shifts instead of a loop with variable 32-bit shifts.

The MD sprite line-mask helper clamps to visible rows once and advances one mask
bit per line. Off-screen rows no longer execute the per-row bounds test; visible
rows avoid recomputing a variable 32-bit shift. SAT order and the eight-entry
budget, including transparent and off-screen-X sprites, remain unchanged.

## Measured full-game results

| Measurement | V42 | V43 |
| --- | --- | --- |
| Idle updates / 300 physical gameplay frames | 227 | 227 |
| Reference route gameplay physical frames | 571 | 529 |
| Sampled route gameplay updates | 346 | 345 |
| Profiled route master cycles | 613517949 | 572321489 |
| Profiled VBlank function cycles | 101435866 | 68898760 |
| Full-game image bytes | 478284 | 478324 |
| BSS bytes | 32296 | 32296 |

The route uses about 7.4% fewer gameplay physical frames and 6.7% fewer profiled
master cycles. Function cycle totals cover different physical-frame counts;
they are not isolated per-call benchmarks. Idle cadence did not improve.
Both finish at cell 94, position [56,104], HP 24, state 0C, as does the SMS
reference. Sampled update counts can differ by one at a physical-frame boundary;
exact input phase and complete game equivalence are not claimed.

The native image checksum is 20D7; RAM ends at FF7E28. Actual linked vectors,
header/checksum, writable placement and native-only checks pass. No extra
persistent RAM is used. Audio and hardware VBlank checks pass on both routes.

## Validation

The independent host pixel/scanline oracle passes all 6951 sprite-status cases.
A generated Z80 program on the independent SMS II hardware core passes all
1024 Y/height/zoom collision cases, directly matched by the modified portable C.
The MD helper oracle passes 18688 mask/count cases and 98304 pixels.
Both modified helpers pass ASan/UBSan with leak detection disabled because of
the existing process-inspection restriction. Original full-IRQ differential,
final compatibility, VDP-block, compiled coverage, portability and backend
checks pass. All 536 production-backend raster stages / 30736384 pixels pass against the
independent oracle. Fixture size is 10328 bytes, BSS 25947, checksum 1B4E.

The settled full-game V43 capture differs from V42 at 363 of 49152 viewport
pixels despite equal final cell/position/HP and sampled frame-counter value.
Additional idle ticks did not establish exact screenshot equality. This test
is therefore not signed off as a full-game pixel-equivalence check. The
synthetic backend oracles and instruction differential suites remain passing;
full-game upload/animation phase comparison needs further work.

## Remaining work

Further profile uploads and sprite metadata at idle and during scrolling.
Combined fine H-scroll/right V-lock, exact overflow timing, combat/interactions,
SRAM round trips, full playthrough and hardware/PAL/NTSC checks remain open.
