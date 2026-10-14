# Live key-door gameplay and persistence - unchanged v0042

ROM: [gaw-megadrive-v0042.bin](../versions/v0042-2230c2b4/gaw-megadrive-v0042.bin).
SHA-256: `2230c2b4badf9c0086cfcd0fd2ca45cea0e8942a79631252ee24306ddd8409ff`.
No production source or ROM change was necessary for these additional checks.

The production cartridges boot normally and enter a dungeon through normal
controller input after a controlled exterior fixture. A second fixture supplies
real room 120 or 121, its map, starting position and inventory. Subsequent input
opens top/left/right doors, traverses to the adjacent room and returns, through
the actual gameplay loop. The original room scripts for the selected rooms are
RET at B761; no script, dispatch, redraw, IRQ or ROM instruction is patched.

Eighteen cases pass across NTSC/PAL: three directions and ordinary keys,
master key or empty inventory. Successful crossing and return have matching
room, hero position, remaining keys, all 256 room flags, cells and map words at
the first resumed gameplay frame. Empty inventory refuses opening. Repeated
held contact consumes only one ordinary key; the master key preserves all five.

Eighteen further cases force death after that path and use normal menu input
for Continue. Both machines resume at checkpoint 1F0 with matching room/state,
hero position, remaining keys, all persistent room flags and map data.

Two save/cold-load cases transfer the controller-generated right-door state
(ordinary/master key) to the established save-point route using a RAM fixture.
Production save menus write slots 1/2, and a fresh emulator invocation loads
each SRAM image through normal menus. The complete 592-byte saved record matches
the SMS, and all 256 flags, ordinary keys and master-key ownership survive cold
loading. The emulator trims trailing FF SRAM bytes; comparisons normalize that
unused tail and the Mega Drive odd-byte SRAM lane, as in the existing save tests.
The route from dungeon to save point is not an uninterrupted verified playthrough.

The opening decision occurs at the same frame on SMS/MD in all successful
cases. Full timing remains imperfect. First crossing gameplay resumes 4..8
frames early on NTSC and 3..6 early on PAL. Return offsets range from one frame
early to five late because the fixed input schedule starts the return from
different positions after the initial timing difference. This is evidence for
further redraw/loading work, not a claim of exact animation speed or pixels.

Five additional reports and their input-state provenance are bound by the
[audit](../versions/v0042-2230c2b4/key_gameplay_patch_audit.json).
Natural travel to the controlled rooms, other puzzles, room-clear triggers,
remaining enemies, bosses and ending remain incomplete. Next: profile original
5E90/1DE2 redraw timing, then continue room-clear and puzzle scripts.
