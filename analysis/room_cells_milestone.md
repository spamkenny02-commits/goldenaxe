# Persistent room reconstruction - v0041

ROM: [gaw-megadrive-v0041.bin](../versions/v0041-d8f2dc05/gaw-megadrive-v0041.bin).
SHA-256: `d8f2dc050dd1b46f59370599da09c40f444908040bb5a0dcb287f7e89e752ffd`.
Size: 524288 bytes. Additive checksum: `D52E`.

Room loading now applies the original persistent cell transformations before
building collision/playfield maps. The extractor preserves the 111 exterior/
house records at BB62 and 73 dungeon records at BD1F. Native preparation ports
1976, all 21 transformations selected by 1A7C, and the visited/door flags in
1BCD. Cell changes feed both SMS tile words and their Mega Drive conversion.
This runs for door loads, dungeon/exterior scrolling and checkpoint loading.

The persistent flag mask depends on graphics class: exterior bit 01, house
bit 02 in its parent room, dungeon bit 04. Dungeon visited bit 10 is retained.
Bits 20/40/80 reconstruct the top, left and right passages before the selected
metadata transformation. Supporting tiles and multi-cell transformations use
the source order and positions.

A separate SMS fixture executes unchanged original routines 1976/1A7C/1BCD/
2279, with original map/metatile decoders, for 512 rooms and sixteen flag values.
The native harness includes exact copies of production sources and calls their
map preparation. All 8192 cases match: 1,310,720 playable cell bytes and
20,971,520 combined SMS/MD map bytes, plus metadata and persistent room flags.
All 21 transformation types are exercised. House cases set the flag in parent
room 94 while leaving the interior flag clear, checking the parent selection.
The SMS fixture changes only boot, fixture space and RST28's EI instruction;
the original routines being compared remain unchanged.

Current merchant, dungeon entry/exit, death/Continue, dungeon/exterior scrolling
and movement regressions also pass in the checked regions. Twelve reports are
bound to the cartridge by the [audit](../versions/v0041-d8f2dc05/room_cells_patch_audit.json).

This reconstructs persisted room states; it does not yet implement natural
puzzle activation or key consumption. Fixtures initialize flags directly.
Only the 160 playable cells and 640 playfield words are compared. Original
out-of-playfield scratch/queue effects are excluded; native reconstruction
bounds its cell writes to the playable map. Exterior quest/portal processing
after 1976, remaining enemies, bosses and ending remain incomplete. Dungeon
transition timing, lantern activation and complete tile animation are pending.

Next: connect persistent flags to original room scripts and natural actions,
starting with dungeon key doors and room-clear triggers, then verify re-entry
and save/Continue persistence along real gameplay routes.
