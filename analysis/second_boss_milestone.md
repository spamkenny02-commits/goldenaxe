# Type65 boss with eight satellites: v0111

ROM `versions/v0111-26d75abb/gaw-megadrive-v0111.bin`, 1 MiB,
SHA-256 `26d75abb554ed062e218a2e3d48fff120abcd08f28b7f9a6a1f220e5cb188b7d`,
checksum 24A5. This is the second boss behavior translated, not a claim about
its chronological position in a playthrough. Its room-list entry is 0163.

## Native implementation

- Core type65: fixed entry 5071, bank2 state table A86D, states 0/2/4/6/8.
  Initialization at (128,80), 48-tick flash, eight satellite creation, movement,
  twenty movement segments before possible random pause, 64..127 pause ticks
  including the same-call decrement, then movement resumes.
- Original eight-way selection 4EB7, hero-relative choices and nibble-aligned
  room limits 4E0A translated. Literal 32-byte turn table and two 41-byte
  movement tables extracted without modification. Eight-pixel segments last
  16 ticks with satellites, eight ticks without them.
- Wrapper 5077..512A always counts all eight transient records, including death
  particles. Center collision is enabled only when that count becomes zero.
  Orbital phase advances by two with >=4 occupied records, otherwise four.
  Radius follows original asymmetric boundary handling. Offsets use the existing
  original signed sine table and doubled multiply/high-byte arithmetic.
- Satellite type66: 512B initialization, HP12/attack10, center-relative byte
  coordinates, visibility/contact disabled outside X[25,232),Y[17,152).
  Surviving hit/death particle behavior uses the existing native damage path.
  Core and satellite collision descriptors publish after behavior like 0940.

## Validation

`validate_second_boss.py` runs 1,138 original/native routine cases: 888 core,
250 satellite. All 768 actor bytes match. Covers five core states, selected
timer/flash/occupancy boundaries, direction choice and limits, twenty-segment
countdown, every initial orbital phase 0..255, extreme radii and coordinate
wrapping. Not the Cartesian product of all possible actor field values.

The SMS fixture changes three LD A,R instructions to explicit B/C inputs and
replaces only the random-byte routine 04E1 with an explicit fixture input. All
other relevant original behavior, selection, bounds and trigonometric arithmetic
execute unchanged. Production uses provisional SGDK random() values; this test
does not prove equivalence of random sequences.

`validate_second_boss_gameplay.py` compares 12 controlled production-loop
segments across PAL/NTSC: appearance, eight/three/zero satellites, movement,
and lethal pending damage to all satellites. All 768 actor bytes match for 882
frames. Shield destruction exercises the native and original explosions and
eventual center vulnerability. Loot outside the actor array is not compared.
Fixtures initially use an exterior and stop before random movement selection.

`validate_second_boss_entry.py` enters the real room0163 by a normal right scroll
from a controlled room0162 boundary, after executing a normal dungeon doorway.
Original destination scripts, map/resource loading and actor creation execute.
Both regions match 47 actor frames aligned to initialization and all 20 loaded
sprite tiles at three relative frames. It does not prove absolute loading timing
or a naturally traveled route. Captures show the boss and orbiting satellites in
the actual room; later random motion can differ.

Patch audit confirms main.c and first-boss resources unchanged, all three literal
tables exact, and actor changes limited to type65/66 behavior/dispatch/collision
publication. First-boss 1,789 routines and six production segments, ordinary
timing PAL/NTSC, six inventory returns, and two boss-death/gem chains pass again.

## Remaining scope

Original refresh/RNG, naturally reached full fights, exact SAT/framebuffer/audio
and full hardware timing remain unproved. Earlier upward/slow scroll differences
and first-boss already-full fan inherited-IY side effect remain open. Other bosses,
quests, ending and complete natural playthrough are unfinished. Next boss entry
to examine: type67 fixed5193 and bank2 A972 composite state table.

Reproduce: extract_second_boss.py; build.ps1; validate_second_boss.py --generate;
build_second_boss_harness.ps1; validate_second_boss.py;
validate_second_boss_gameplay.py; validate_second_boss_entry.py;
audit_second_boss_patch.py. Regression tools/reports are preserved in the archive.
