# V29 — First native Mega Drive execution

Built Genesis Plus GX at 49c584764893b0505ac7f768a754f97330fa4392 and added a
stdlib-only libretro harness. It drives the physical controller interface,
reads the native ELF's RAM symbol, captures private screenshots and measures
audio/game progression. Native 68000 boot reaches title, name creation,
new-game setup and 300 emulator gameplay frames at cell 95 with HP 24 and
PSG peak 5,244. This validates that path, not a full-game playthrough.

Execution exposed a disabled-display deadlock: VBlank status remains set
throughout a blanked MD frame. The barrier now uses the running VCounter.
An enabled horizontal Window had hidden Plane A, and Plane B aliased the
opaque Window table. The Window now covers only rows 24-27 and Plane B uses
an independent transparent tile/table. Empty SAT clears stale sprites;
wrapped SMS Y positions are converted correctly. Colors use DAC levels
0/2/5/7 instead of stopping short of white.

A mathematical 256-entry lookup converts planar rows into packed MD pixels;
unchanged shadow writes do not request redundant hardware uploads. Independent
checks cover 5,120 rows, 64 colors, 8,192 descriptors and 256 sprite positions.
Standalone video, presentation, full IRQ, intro and native-only boot regressions
pass. The 433,646-byte image cross-links with BSS 25,152 bytes in work RAM and
checksum 6CD6. All twelve states, audio and IRQ remain interpreter-free.

The initial C backend still advances fewer game frames than physical emulator
frames. MD asynchronous/line IRQ scheduling and performance work are next,
along with five presentation hooks. Hardware testing remains outstanding.
Screenshots, private ROM and emulator state are ignored build outputs.
