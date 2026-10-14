# Source-derived title loading - v0017

ROM: `versions/v0017-e44647ec/gaw-megadrive-v0017.bin`.

This continues v0016's title cadence correction. It restores the time spent by
the original title loader instead of exposing the native decoder's faster
completion. `title_loading_cost.py` counts the source instruction loops and
packed resources; `extract_title.py` generates the foreground-cycle metadata.
There is no captured state or Z80 execution in the native cartridge.

| Source section | Z80 T states |
| --- | ---: |
| Clear previous screen, 0B56..0B91 | 95,572 |
| Bank and palette setup, 1473..1487 | 401 |
| Pattern and both map decoders | 2,269,572 |
| Initial colors and tilemap upload, 1499..14CF | 50,086 |
| Total | 2,415,631 |

The RLE pattern decoder costs 2,058,555 T states. The two map decoders cost
101,616 and 109,320 T states. Each component and the full total match live
source execution exactly in both regions, after removing observed IRQ cycles.
`genesis_plus_gx_title_libretro.dll` is a separate read-only diagnostic core;
the previous actor-timing DLL and PSG diagnostic DLL remain unchanged.

The native loader derives a 43-frame NTSC / 36-frame PAL foreground budget
from that instruction count and a 3,072-T-state-per-frame IRQ reserve. Native
VBlanks already consumed by decompression, conversion and upload count toward
the budget. Remaining time is spent with a black screen. The original one-IRQ
black-palette wait before the display is enabled is also restored. The IRQ
reserve is an approximation; this does not emulate every interrupt phase.

The natural-boot comparison now measures exactly the same interval between
intro completion and first cape pose: 86 video frames in NTSC, 79 in PAL.
All 42 title map states retain identical intervals and all 18 palette states
retain identical values and intervals. Eighty representative actual video
captures match after color normalization, across PAL/NTSC and with/without
skipping the intro. Palette RAM changes and queued map transfers can differ
by one frame at a boundary; cycle-level visual synchronization is unproven.

Absolute boot timing remains unfinished. The natural title map has the same
constant offset as the preceding story: 12 frames late in NTSC and 6 early in
PAL. The long held intro-skip input also differs because the native port waits
for release before accepting a title press; its title maps are 21 frames late
in the controlled skip test. No arbitrary adjustment is applied to hide these
separate causes.

The latest binary also passes the 65-line intro/scene-map checks, hero and
three exterior-scroll timing comparisons in both regions, and the seven
merchant interactions and reveal checks. These are targeted checks, not a
complete game validation. `title_patch_audit.json` binds all eleven reports;
`title_loading_model_report.json` includes complete source profiling evidence.

Previous numbered ROMs remain immutable, including v0016 for comparison.
