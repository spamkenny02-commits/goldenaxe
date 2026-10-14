# Dungeon entrances - v0039

ROM: [gaw-megadrive-v0039.bin](../versions/v0039-ece4a6b0/gaw-megadrive-v0039.bin)

SHA-256: `ece4a6b0c171afb03fb04e680515df12b27601a07755a9f9210a2980622db70c`.
Size: 524288 bytes. Additive cartridge checksum: `5A47`.

The production 68000 cartridge now dispatches the ten unconditional dungeon
entrances extracted from the original Z80 room scripts. It loads class-2
graphics, maps and per-dungeon palettes, records the visited flag and dungeon
checkpoint, selects dungeon music, and returns through the ten standard exits.
Actor persistence uses the original low-byte room indexing and resets on entry
and exit. Continue after death restores the dungeon checkpoint at the original
center position, with the compared health, magic and money values.

Forty controlled cases compare entry/exit or entry/death/Continue against the
original ROM, ten of each in NTSC and PAL. These exercise real controller input
and production door dispatch after initializing the exterior room/map/position.
Settled state, 256-byte persistence masks, base cells, maps, visited flags, music
and the first thirteen palette colors match. The animated palette colors belong
to the original cycle; their phase is not asserted exact.

The separate native loader harness exercises all 512 room loads, including 256
dungeon rooms, ten dungeon palettes and 38 dark rooms. The original Z80 decoder
harness independently verifies all 512 base maps. Current merchant, exterior
scrolling, movement, title and intro regressions also pass. The audit binds all
fifteen reports and compiled entrance/resource arrays to this ROM hash.

This is an entrance milestone, not a playable full dungeon progression.
Dungeon scrolling remains disabled. Conditional cells, keys, puzzles, quests,
remaining enemy behaviors, bosses and ending remain incomplete. Natural routes
to these entrances have not been tested. Entry fades and loading timing are
not source exact. Dark rooms load unlit; lantern activation and full tile
animation remain incomplete. The 576 decoded animation bytes are a source SRAM
cache, not a verified initial VRAM upload.

Evidence: [audit](../versions/v0039-ece4a6b0/dungeon_doors_patch_audit.json).
