# V56 — homing projectile verified against original Z80

768 new type-117 differential cases cover states 2/4, signed velocities at
and around the three-pixel limit, four arena boundary coordinates, contact
flag switching, returning-to-boss overlap and lifetime values 1/47/48/192.
Every compared RAM byte matches the unaccelerated original Z80 handler.
The suite passes 5792 boss-phase, 2530 death/reward, 256 spell-projectile,
768 homing-projectile and 2816 loot cases. 47 tooling tests pass.

Three controller experiments were rejected and reverted. Waiting for all
homing projectiles to return regresses MD dungeon 9 to five boss hits;
allowing moving-phase finishing swings gives the same 13 hits as V55;
reserving a longer invulnerability window for swings still stops at 13.
The checked V55 controller and its optional patient mode are retained.
No production C/ROM change or native dungeon-9 completion is claimed.

The V55 selective-fire controller still dies at $16A in SMS dungeon 10.
Native MD reaches $17B alive with 12 HP / 16 MP and no live enemies, but
cannot reach the stairs before timing out at 90000 frames. The screenshot
and descriptor buffer show disconnected regions in that room.

The route missed a remote switch: `world_run_finalize_special_callback`
for $B586 (room $17C) sets progress bit 2 in $17B. Entering $17B from $17A
puts the hero in its western region, unable to reach the eastern exit.
The corrected generator now uses $17A->$18A->$18B->$17B (south entry),
then $17C's switch at [184,40], returns to $17B and takes the stairs to $13C.
Only route 10 changes; routes 1..9 are byte-for-byte unchanged as JSON data.
The route continuity and dependency tests pass. Native traversal of the
corrected route is running; no completed switch/traversal claim is made.

A combat-target clamp was rejected: it preserves the SMS dungeon-9 pass
but makes SMS 10 die earlier, at $14D. The V55 controller is retained.
Native dungeon 9 remains at the V55 patient-probe result, 13 of 15 hits and
12 boss HP remaining. SMS dungeon 9 remains validated.

Private reports stay ignored under md/build/v56_*. Original ROMs, captures,
RAM dumps and built binaries are not published. See dungeon_traversal_v56.json
for counts, failed attempts and hashes.
