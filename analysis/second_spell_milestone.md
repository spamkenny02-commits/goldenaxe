# v0084 - second offensive spell (inventory slot 5)

Native 68000 translation of original activation 3077..30A6, behavior 3A27..3B07 and terrain writes 3591/35B7. ROM remains 1 MiB. No embedded Z80 gameplay execution.

Slot 5 now spends eight magic per cast, preserves selection on insufficient magic, refuses a second active auxiliary projectile, uses four directional velocities and a two-tick animation period. Fire remains slot 4 with its original charge cycle. The shared 48-byte projectile record, collision boxes and sprite descriptor are retained.

Two terrain probes execute per update, including the second probe after a successful first probe. Dungeon, exterior level-1 and higher-level replacement tables are extracted directly from the original ROM (54 bytes total). The higher-level table falls through into the level-1 records. First/below cell replacements update mutable cells, the software name table and the actual Mega Drive map. Special metadata cells set the persistent progress flag before preparing dependent cells. Interior class 1 uses the parent room for the flag, matching 193D; this last correction distinguishes v0084 from intermediate v0083.

## Current evidence

- 22 controlled slot-5 cases: four directions, two levels, insufficient magic and recasting, PAL/NTSC. Full 48-byte projectile record, seven hero fields and 160 terrain cells match for 121 frames per case. Active projectile tile pixels match.
- 20 controlled terrain cases: replacement/fallthrough/rejection and dungeon table dispatch. Software map, terrain, magic and projectile record match for 61 frames; stable actual hardware maps match (1,280 bytes after attribute conversion).
- Four controlled room-09 special-cell cases: fresh/already-set persistent bit, PAL/NTSC. The conditional replacement and final persistent flag match the original.
- 22 fire regression cases: 20 match all compared source states. Two insufficient-magic PAL cases have one frame of differing hero attack strength (source 4/native 2 at frame 2810). The exact byte-for-byte rebuilt v0082 exhibits the same discrepancy. Projectile records, terrain and active projectile tile patterns match.
- Existing movement/three scroll-direction/eight deterministic-enemy checks pass in both regions.
- Audit reconstructs v0082 main.c and actors.c exactly when only the declared spell changes are reversed; prior resources remain unchanged.

## Known limits

Ownership, position, clock, terrain and enemies are controlled in these tests. Dungeon dispatch uses exterior resources with a controlled room high byte. These checks do not establish natural spell acquisition, combat damage, a full dungeon route, natural special-room arrival, save/re-entry or a complete playthrough.

Fire full-frame images still differ. An exact v0082 rebuild and current v0084 both differ from SMS by 190 normalized pixels at frame 3749 in one up-fire sequence. At frame 3751, v0082 differs by 25 and current by 30 pixels. This is diagnostic evidence, not passing image equivalence; beam/transfer timing needs further investigation.

Audio waveforms, global timing, remaining abilities, full enemy/boss behavior, quests and ending are unfinished. Targeted checks do not establish a complete faithful port.
