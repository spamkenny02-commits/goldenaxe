# V56 — homing projectile verified against original Z80

768 new type-117 differential cases cover states 2/4, signed velocities at
and around the three-pixel limit, four arena boundary coordinates, contact
flag switching, returning-to-boss overlap and lifetime values 1/47/48/192.
Every compared RAM byte matches the unaccelerated original Z80 handler.
The suite passes 5792 boss-phase, 2530 death/reward, 256 spell-projectile,
768 homing-projectile and 2816 loot cases. 46 tooling tests pass.

Three controller experiments were rejected and reverted. Waiting for all
homing projectiles to return regresses MD dungeon 9 to five boss hits;
allowing moving-phase finishing swings gives the same 13 hits as V55;
reserving a longer invulnerability window for swings still stops at 13.
The checked V55 controller and its optional patient mode are retained.
No production C/ROM change or native dungeon-9 completion is claimed.

The current saved selective-fire controller is being tested through dungeon
10 on original SMS and native MD; these runs were not previously completed
for V55. Native dungeon 9 remains at the V55 patient-probe result, 13 of 15
hits and 12 boss HP remaining. SMS dungeon 9 remains the validated V55 pass.

Private reports stay ignored under md/build/v56_*. Original ROMs, captures,
RAM dumps and built binaries are not published. See dungeon_traversal_v56.json
for counts, failed attempts and hashes.
