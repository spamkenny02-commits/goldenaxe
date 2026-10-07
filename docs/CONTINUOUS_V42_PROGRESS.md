# V42 — Recover full-game validation and cache physical scroll tables

Recovered the previous local reference ROM, m68k-elf toolchain and instrumented
Genesis Plus GX core. A fresh checkout of V41 was rebuilt first. No reference
cartridge bytes or full-game binary are committed to the public repository.

## Backend change

Skip rebuilding the physical H-scroll/VSRAM tables when SMS scroll registers
and scroll-lock flags have not changed. Invalidate on platform init and the
$0275 line handler, which overwrites physical H-scroll without modifying the
SMS shadow. Four bytes of persistent state are added; no interrupt-stack
buffer is added.

Four new ROM-free production-backend stages exercise nonzero H-scroll, its
restoration after the line handler, top-16-line H-lock and physical backend
reinitialization while scroll is unchanged. Every stage waits repeated physical
frames, exercising the cache-hit path. All 536 stages / 30736384 independent
pixel comparisons pass locally. The fixture is 10200 bytes, BSS 25947,
checksum 0D37. Combined fine H-scroll/right V-lock remains unverified.

## Full-game measurements

| Measurement | Rebuilt V41 | V42 | Original SMS |
| --- | --- | --- | --- |
| Full-game bytes | 478160 | 478284 | not applicable |
| BSS bytes | 32292 | 32296 | not applicable |
| Idle updates / 300 gameplay frames | 227 | 227 | not rerun idle |
| Route gameplay physical frames | 571 | 571 | 348 |
| Route sampled gameplay updates | 346 | 346 | 346 |
| Final cell / position / HP / state | 94 / [56,104] / 24 / 0C | 94 / [56,104] / 24 / 0C | 94 / [56,104] / 24 / 0C |

V42 checksum is 61A4; writable RAM ends at FF7E28. Actual linked vectors,
header/checksum, RAM placement and native-only interpreter exclusion pass.
The final 256x192 gameplay captures agree at all 49152 pixel positions under
a bijective 21-colour palette mapping. Raw RGB intensities differ between
the SMS and MD DACs; this is one settled viewport, not a full-game raster claim.

PSG audio peak is 6044; idle hardware IRQ deltas are 299 VBlanks / 300 frames.
The cache avoids redundant transfers but produces no measured cadence gain on
these routes. V37's documented idle rate was 239 updates/300 frames. Correct
sprite copies therefore still warrant performance work. Exact input/frame
phase and full-game equivalence are not claimed.

All existing host differential/regression targets and compiled registration
coverage pass with the verified private reference input. Portability/backend
checks, ROM-free conversion/status/block/sprite tests and extraction-tool tests
pass. The complete `make test-sanitize` suite also passes with ASan/UBSan and
`ASAN_OPTIONS=detect_leaks=0` (the existing local LeakSanitizer process-inspection
restriction remains). Native boot links and runs without the interpreter.

## Next work

Profile sprite-copy/shadow overhead, validate combined fine horizontal scroll
and right-column V-lock, then continue combat/interactions, SRAM round trips,
full playthrough/ending, exact overflow timing and PAL/NTSC/hardware checks.
