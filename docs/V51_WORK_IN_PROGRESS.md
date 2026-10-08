# V51 dungeon driver work

Restored the exact published V50 commit bb49308c9efde72bb2f646109932b451850597a6
on 2026-10-08 after the workspace reverted to an older local draft. The older
files are preserved in a git stash and private md/build/recovery_20261008/.
The V50 build reproduces 484504 bytes / checksum BB38.

Verified again: 354 merchant cycles, 38 world-item cases and 144 full effects.
Dungeon 7 native MD now completes: 21 visits, 3 stair passages, 6 genuine
full-HP boss hits, crystal acknowledged, outside exit, final HP 128 in 24030
emulator frames. Reports are ignored under md/build/v51_dungeon7/.

Driver fixes under current integration validation:
- Price destructible terrain using the actual collision probes, rather than
  the player center's tile; otherwise a short route wasted magic on blocks.
- Include room/equipment/destructive-magic availability in the navigation
  cache key so terrain permission changes do not retain an invalid path.
- Advance an expected arrival before considering retreat recovery. An intended
  A -> B -> A detour was mistaken for a retreat and looped forever in MD 5/6.

15 tooling tests pass, including targeted terrain and planned/unplanned
backtrack cases. Current full MD/SMS 5/6/7 runs are in
md/build/v51_dungeons567/; these must pass before declaring new route coverage.
All fixture preparation is one-time; later RAM writes remain forbidden.
No original ROM, captures or compiled binaries are committed.
