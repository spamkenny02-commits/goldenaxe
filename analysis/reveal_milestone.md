# First-scene intro reveal cadence - v0030

ROM: `../versions/v0030-c325609b/gaw-megadrive-v0030.bin`.

The old reveal reconverted all four planes and uploaded 288 tiles by CPU for
every mask. Live hardware VRAM showed eight frames between successive mask
starts in NTSC and six in PAL; the source takes five in both regions.

The native routine now updates only plane 3 in the already converted patterns.
Four-row groups precompute the mask rotation and avoid repeating conversion
work. Transfers use the VBlank DMA queue and source-derived row slices:
100 Z80 T-states per row, initial V-counter range 112..192, regional frame
budgets and an approximate 3600-T-state interrupt allowance. Actor/palette
behavior still runs once per mask pass; music IRQs continue every frame.
The shared routine serves all three scenes, but direct hardware reveal cadence
verification in this milestone covers the first scene only.

`profile_intro_reveal.py` reads serialized hardware VRAM without game mutations,
reconstructs SMS planar graphics from native packed tiles and compares all
9216 bytes after each of eight completed masks. All sixteen region/mask pairs
match. Both systems start passes five frames apart and complete each pass on
its fifth sampled frame.

This does not establish exact scanline rendering. Relative progress differs
by up to 35 rows in NTSC and 15 in PAL during partial transfers. Native first
mask starts at frame 57 versus source 69 (NTSC), and 48 versus 62 (PAL).
Bootstrap/loading therefore still starts 12/14 frames early. No compensating
constant delay was introduced; source loading costs remain to be translated.

The full natural intro still matches all 65 text/scene tilemaps and returns to
the title in both regions. Text starts remain 10..11 frames early in NTSC and
12..13 early in PAL, without accumulating delay. Title cape/warrior/logo cadence
and sampled pixels pass with both a skipped and natural intro in both regions.
Movement and four-direction scroll-object regressions pass in PAL and NTSC.
`validation/reveal_patch_audit.json` binds eleven reports and verifies cartridge
checksum and aliases. Versions 28/29 are intermediate builds; version 30 is the
verified result. Version 27 remains available.

Remaining work includes bootstrap timing, partial scanline equivalence, direct
measurement of scenes 2/3 and their sprites, conditional story/dungeon behavior,
sprite-overflow allocation suppression and full-game progression.
