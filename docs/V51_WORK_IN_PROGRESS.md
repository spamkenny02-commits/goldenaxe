# V51 — verified dungeon checkpoint, work continues

## Recovery

Restored the exact published V50 commit bb49308c9efde72bb2f646109932b451850597a6
on 2026-10-08 after the workspace reverted to an older local draft. The older
files are preserved in a git stash and private md/build/recovery_20261008/.
The V50 build reproduces 484504 bytes / checksum BB38. This checkpoint changes
only the controller driver, tests and documentation; production C is unchanged.

## Controller fixes

- Price destructible terrain using the actual collision probes, rather than
  the player center's tile; otherwise a short route wasted magic on blocks.
- Include room, equipment and destructive-magic availability in the navigation
  cache key so terrain permission changes do not retain an invalid path.
- Advance an expected arrival before considering retreat recovery. An intended
  A -> B -> A detour was mistaken for a retreat and looped forever in MD 5/6.
- Escape grabbing type-91 enemies before attacking. Choose a reachable retreat
  when a wall blocks the direct escape, maintain distance and use ranged fire.
  The original also leaves the hero grabbed if the attached enemy dies; six
  new handler/death scenarios compare both routines against original Z80
  instructions (12 comparisons), including assertions for that boundary.

## Fresh validation

17 tooling tests pass, including collision-probe cost, cache invalidation,
planned/unplanned backtracks, grab release and escape blocked by a wall.
All 5004 combat comparisons pass: 2688 collisions, 1152 damage/death/recoil,
1152 entropy-replayed AI and 12 grab/death boundaries.
Also reverified V50's 354 merchant cycles, 38 world-item cases and 144 full
effects. Merchants, items and production magic fixes remain covered.

The latest driver passes the strict dungeon validator on both backends:

| Dungeon | Backend | Visits | Stairs | Full-HP boss hits | Net keys spent | Final HP | Emulator frames |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | Native MD | 27 | 2 | 8 | 1 | 114 | 25355 |
| 5 | Original SMS | 27 | 2 | 8 | 1 | 112 | 8052 |
| 7 | Native MD | 21 | 3 | 6 | 2 | 126 | 26338 |
| 7 | Original SMS | 21 | 3 | 6 | 2 | 122 | 9020 |

Each run confirms the ordered route, actual full-HP boss damage and death,
crystal collection/acknowledgment, stair passages, survival and return to the
outside with dungeon index zero. Different timing and HP are reported rather
than treated as identical emulator traces. Reports are private/ignored under
md/build/v51_dungeon5_reachable_escape/, md/build/v51_dungeon5_sms/ and
md/build/v51_dungeon7_final/.

All fixture preparation is one-time outside the entrance; later RAM writes
remain forbidden. These equipped checkpoints do not establish item acquisition
or a fresh uninterrupted playthrough. V50 validated MD dungeons 1-4 and the
final boss/credits/title sequence separately; they were not repeated here.

## Remaining traversal work

- Native dungeon 6 advances beyond the former 138/139 loop but the pilot dies
  in room 125 before its earth-magic puzzle. Full traversal is not validated.
- Dungeon 8 advances beyond the former switch loop, then reaches a closed
  left gate in room 1D8. Route/gate analysis is still required.
- Dungeons 9 and 10 remain incomplete as traversal routes. Earlier full-HP
  boss arena and ending tests remain separate evidence.

## Reproduction

Use the normal native build and private original SMS ROM with:

```sh
python3 -m unittest discover -s tests -p test_tools.py
make test-combat test-merchants test-world-items test-full-effects
python3 tools/test_md_dungeon_emulator.py --core "$CORE" --nm "$MD_NM" \
  --reference-rom "$SMS_ROM" --dungeons 5 7 --frames 60000 \
  --output md/build/v51-recheck
```

CORE is the Genesis Plus GX libretro core, MD_NM the m68k-elf-nm path, and
SMS_ROM the privately supplied original ROM. No original ROM, captures,
compiled binaries or RAM dumps are committed.
