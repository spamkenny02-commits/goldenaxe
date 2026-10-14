# Dungeon actor assets and walkers 43..45 - v0033

ROM: `../versions/v0033-86a5a66c/gaw-megadrive-v0033.bin`.

Actor extraction previously covered only the 256 exterior room lists. It now
includes the 512 source lists and all 80 graphic types, with 89408 bytes of
planar graphics and their native packed counterparts. Pattern offsets are
32-bit big-endian entries: 16-bit offsets cannot address the complete set.
The production actor loader consumes these offsets and retains room-layer
information for shared projectile bounds. The cartridge still fits 512 KiB.

Types 43/44/45 follow source 984F..98F8: terrain00 emergence, quarter-pixel
movement for 43 and half-pixel movement for 44/45, source counters, direction
selection, pursuit along the axis with greater distance, and equal-distance
direction retention. A blocked preferred direction preserves the current one.
Types 44/45 can emit projectile70 through the SMS overflow guard at 98F1;
43 does not fire. The original RNG stream is not reproduced.

Projectile70 uses the exact 4399..43AE template and shared 3DFA lifetime/bounds.
Shared projectiles now apply dungeon bounds when the room layer is 1:
Y32..135 and X32..223, retaining exterior Y8..151/X8..247 bounds otherwise.

Live source/native tests in PAL and NTSC compare 48 nonrandom state/direction
cases, 24 blocked directions, 288 source-observed controlled random decisions
and eight projectile trajectories per region. All 11616 actor-record comparisons
match, excluding renderer collision-list descriptor bytes 27/28. Appearance
tests compare three accepted terrain00 placements and twelve terrain refusals
per region with explicit native RNG/clock fixtures.

A separate test-only SGDK cartridge compiles copies of the production actor
loader and data. It calls the native 68000 loader for all 512 rooms with masks
FF/A5/00, holding each result for hardware frame ticks so observations are stable.
All 1536 cases match the ROM-derived source loader reference: 1179648 actor bytes,
50331648 planar/packed graphic bytes, allocation and actor counts. This executes
the native C loader; it does not navigate the source game through every room.
The harness source copies and binary hash are retained in its evidence report.

Existing sprite-overflow modeling, enemy40 behavior, movement, four-direction
scroll objects, title cadence and the 65-line natural intro checks pass. The
dungeon_walkers_patch_audit.json binds fifteen current reports, checks all
eighty graphics/index entries against source data, and verifies cartridge
checksum/aliases. Older ROMs remain available.

This supplies the assets and first dungeon behaviors, not complete dungeon
gameplay. Natural dungeon entrances/maps/progression, conditional story objects,
remaining enemy/boss behavior, combat with the new projectile, full ending and
the earlier intro timing limitations remain to verify or implement. Loading
graphics for a type does not mean its behavior has been ported.
