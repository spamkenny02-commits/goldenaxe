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

## Second checkpoint — 2026-10-08

The driver now collects genuine MP/HP drops, charges travel paths for proximity
to active enemies, invalidates paths when those enemies move, and allows melee
approaches to ignore that travel penalty. It prioritizes type-83 armor curses
and type-91 grabs, keeps its distance and reserves more MP during ordinary
ranged combat. 20 tooling tests pass, including enemy motion/approach and the
new dungeon-8 dependency.

The eighth dungeon's western gate in 1D8 is opened by the $B5BA switch in 19A.
The generated route now visits 1D8 -> 1E8 -> stairs 1AA -> 19A and returns to
1D8 before trying that gate. The original callback sets the room's progress bit;
no gate or progress RAM is patched by the driver.

| Dungeon | Backend | Visits | Stairs | Boss hits | Net keys spent | Final HP | Frames |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | MD | 27 | 2 | 8 | 1 | 116 | 23071 |
| 5 | SMS | 27 | 2 | 8 | 1 | 118 | 8374 |
| 6 | MD | 42 | 3 | 8 | 3 | 98 | 44432 |
| 6 | SMS | 42 | 3 | 8 | 3 | 104 | 14999 |
| 7 | MD | 21 | 3 | 6 | 2 | 126 | 27385 |
| 7 | SMS | 21 | 3 | 6 | 2 | 128 | 9042 |
| 8 | MD | 29 | 5 | 8 | 1 | 114 | 42154 |

All rows passed the strict full-route validator. Reports are private under
md/build/v51_reserve_regression57/, v51_reserve_dungeon6/,
v51_reserve_sms6/ and v51_reserve_dungeon8/.

Updated open issues supersede the earlier remaining-work list:
- SMS 8 reaches the real full-HP boss, but dies after two hits. MP is mostly
  consumed by partition-clearing thunder casts; no full SMS route is claimed.
- MD 9 reaches 1CE with no MP for its required trigger block, then dies.
- MD 10 reaches 16C alive but cannot reach the switch across its partition.
  Eight private one-step comparisons of the original $2DBE player routine
  against native C, with four directions and both equipment states, produced
  no RAM differences at that checkpoint. Further route analysis is needed.
- The production V50 ROM remains 484504 bytes / BB38; only tooling and route
  metadata have changed. Fixture equipment and one-time RAM-write rules are
  unchanged at this checkpoint.

## Third checkpoint — controller recovery and late-dungeon routes

The equipped dungeon fixture now includes one ordinary antidote (C0E2=1),
alongside its original healing potion. The controller selects and consumes it
through the real inventory/item routines after an armor curse. The inventory
request is cleared after consumption, preventing attempts to reselect a missing
item. No RAM writes are allowed after the one-time outside checkpoint setup.

A zero-MP puzzle no longer causes endless failed spell casts: the controller can
fight for actual resource drops. Curse enemies can be attacked in melee once
ranged magic is unavailable. These cases have targeted tooling regressions.

Two more route dependencies are encoded, still awaiting complete traversal:
- $B686 in 1BE closes the western gate during combat and opens the upper gate
  afterwards. Dungeon 9 now follows 1BE -> 1AE -> 19E -> stairs 1CC -> 1BC -> 1AC.
- 16C has disconnected floor regions. Dungeon 10 now takes its stairs to 14D,
  follows the circuit through 13D/13E/16A/17A/17B/13C/13B/14B/15A/15B/16B,
  then reenters 16C from the west before trying its northern gate.

25 tooling tests pass. The combat oracle now also verifies all 32 combinations
of enemy type 92/93 and enemy/hero facing: $5049 cancels damage unless the hero
faces opposite the enemy. Total combat comparisons: 5036. Reliable controller
placement against these enemies remains part of late-dungeon work.

The antidote-enabled SMS 8 pilot passed strict full-route validation: 29 visits,
5 stairs, 8 genuine full-HP boss hits, one net key spent, HP 104, 13637 frames
(md/build/v51_antidote_fixed_sms8/). A fresh MD/SMS 5-8 matrix is being collected
under md/build/v51_release_regression58/ before closing this checkpoint.
The 9/10 pilots remain incomplete; geometric route corrections do not establish
survival or completed rewards/ending through those routes.
