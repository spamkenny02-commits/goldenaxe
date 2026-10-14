# Dungeon world resources and base room loading - v0034

The resource extractor now preserves all 512 base room streams, including
256 dungeon rooms (0100..01FF). The compiled room index has 512 little-endian
16-bit offsets and 48,344 compressed stream bytes. Existing exterior/house
stream ordering and content are preserved.

Source 175F classifies high-byte room IDs as graphics class 2. Source 16D0
selects bank 13: its palette, background stream and metatile stream are now
extracted, together with collision metatiles selected by 825D and animation
selected by 175D. The animation stream initializes 576 bytes, even though
174E copies 1024 scratch bytes; the unspecified remainder is not synthesized.
The native room loader now selects classes 0, 1 and 2 explicitly.

`validate_dungeon_world_assets.py` creates a separate SMS fixture from the
original ROM. Its boot replacement calls unchanged source routines 032A
(VRAM graphics), 0C00 (RAM decompression) and 81C0 (collision metatiles).
RST 28's EI is suppressed only in this fixture to isolate the routines from
the normal game's IRQ handler. Results are held across three VBlank status
polls. All 512 maps (81,920 cell bytes), dungeon background (4096 bytes),
metatiles (648), collision metatiles (40), animation (576) and palette (16)
match resource extraction. Quest-dependent processing after 192A is excluded.

`build_world_loader_harness.ps1` copies every production source file exactly,
including main.c as game_main.inc. A test-only main calls production
load_house_room for each of the 512 rooms, selecting the source graphics
class. The 68000 harness checks decoded cells, collision metatiles, SMS map
words, Mega Drive map words, palette and actual VRAM background uploads.
All 512 loads pass, including all 256 dungeon rooms. These fixtures and
their entry points are never compiled into the production cartridge.

The production cartridge contains all 512 compressed maps. Its normal door
handling still only calls graphics classes 0/1, so LTO may remove unused
class-2 graphics from this cartridge until entrance integration. The separate
native harness proves class-2 loading, not natural dungeon access. Dungeon
entrances/exits, conditional cell edits, puzzles, dungeon scrolling, remaining
actor behavior and bosses still need implementation and progression tests.

PAL/NTSC regressions pass: four-direction object hiding, natural hero and
three exterior-scroll state sequences, eight deterministic enemy movements,
title cape/warrior/logo cadence, and all 65 natural intro text/scene states.
These are focused checks; prior loading/SAT/setup timing limitations remain.
The ten reports and dungeon_world_patch_audit.json are bound to the exact
v0034 ROM, with both aliases, 512 KiB size, ROM end and additive checksum
checked. Older numbered cartridges remain unchanged.
