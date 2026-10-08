# V51 — validated dungeon 5-8 traversal; 9/10 remain open

## Result

Full dungeon routes 5, 6, 7 and 8 pass on native Mega Drive and original SMS.
Every run boots normally and prepares one equipped checkpoint outside the
entrance. All subsequent movement, combat, inventory actions, stair passages,
crystal rewards and outside return use joypad input. Later RAM writes are
forbidden. This validates equipped routes, not item acquisition or a fresh
uninterrupted game.

The production C/MD image is unchanged from V50: 484504 bytes, checksum BB38,
reset vector 000200. No instruction interpreter is linked in production.

## Controller and route fixes

- Terrain costs use the actual collision probes. Navigation cache keys include
  room, equipment, magic availability and moving-enemy positions.
- Expected arrivals take priority over retreat recovery: intended A -> B -> A
  detours no longer loop forever in dungeons 5/6.
- Travel avoids nearby enemies, while melee approaches can reach their target.
  The driver collects genuine HP/MP drops and protects its magic reserve.
- It releases type-91 grabs before attacking, chooses a reachable escape from
  walls, and prioritizes armor-cursing type-83 enemies. With no ranged magic,
  curse enemies can still be defeated in melee instead of endless retreat.
- One ordinary antidote was added to the one-time equipped fixture. The real
  inventory/item routines consume it and restore armor after a curse. The
  selection request is cleared after use, so inventory does not loop trying
  to reselect the consumed item. No consumables are injected during traversal.
- Empty MP at a puzzle causes combat for real drops, rather than endless failed
  earth casts. On the return trip, fire can defeat an unreachable enemy behind
  an E0 partition even below the normal reserve. This fixes the SMS-6 return
  stall in 113 without spending the outbound puzzle reserve.
- Dungeon 8 visits the remote $B5BA switch in 19A before its western gate in
  1D8. Its generated route includes the E8/AA stair detour and the return.

## Strict full-route validation

| Dungeon | Backend | Visits | Stairs | Full-HP boss hits | Net keys spent | Final HP | Emulator frames |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | MD | 27 | 2 | 8 | 1 | 120 | 22957 |
| 5 | SMS | 27 | 2 | 8 | 1 | 118 | 8576 |
| 6 | MD | 42 | 3 | 8 | 3 | 104 | 46537 |
| 6 | SMS | 42 | 3 | 8 | 3 | 68 | 16175 |
| 7 | MD | 21 | 3 | 6 | 2 | 122 | 27864 |
| 7 | SMS | 21 | 3 | 6 | 2 | 128 | 9505 |
| 8 | MD | 29 | 5 | 8 | 1 | 110 | 41006 |
| 8 | SMS | 29 | 5 | 8 | 1 | 104 | 13637 |

Each row passes the strict validator: ordered room crossings, correct dungeon
index, genuine boss HP damage/death, crystal collection and acknowledgment,
survival and outside exit with dungeon index zero. Different timing and HP
reflect different trajectories; identical MD/SMS frame traces are not claimed.
Summaries and controller/route hashes are committed in
[dungeon_validation_v51.json](dungeon_validation_v51.json). Private full reports,
captures and RAM dumps stay ignored under md/build/v51_return_fire_5/ through
v51_return_fire_8/.

V50's previously validated MD routes 1-4 and full final-boss/credits/title-return
sequence remain separate evidence; they were not repeated in this checkpoint.

## Original-instruction checks

26 tooling regressions pass. Combat has 5052 original-Z80/native comparisons:
2688 collision, 1152 damage/death/recoil, 1152 entropy-replayed AI, 12 grab/death,
32 facing combinations for types 92/93 and 16 fire/terrain/direction cases.
The new cases confirm that an attached grabber can die while leaving the hero
grabbed even in the original; $5049 cancels damage unless the hero faces opposite
types 92/93; and fire stops at 80/A0 terrain but crosses E0 partitions.

The restored V50 merchant/item/effect baseline was also reverified: 354 merchant
cycles, 38 world-item cases and 144 complete full effects. The MD ROM checker
passes its size, header, vectors and BB38 checksum.

## Remaining late-dungeon work

- Dungeon 9 now uses the upper exit of 1BE after its $B686 combat callback,
  following AE/9E and the stairs to CC/BC. The former western exit stays closed.
  The pilot reaches AE, but survival against types 92/93 is not validated.
- Dungeon 10 cannot walk between the two floor regions of 16C. Its route now
  uses the stairs to 14D and the circuit through 13D/13E/16A/17A/17B/13C/13B/
  14B/15A/15B/16B, reentering 16C from the west. The pilot reaches 16A, but dies
  before the complete circuit. No completed traversal-to-credits claim is made.
- Reliable placement and resource use against the directional-defense enemies
  remain open. Their original combat rule is covered by the new 32 cases.

All earlier V49 full-HP boss-arena checks remain separate from dungeon travel.
No production collision, damage, gates, HP or progression was relaxed to obtain
these route results.

## Reproduction and recovery

```sh
python3 -m unittest discover -s tests -p test_tools.py
make test-combat
python3 tools/check_md_rom.py md/build/gaw_md.bin
python3 tools/test_md_dungeon_emulator.py --core "$CORE" --nm "$MD_NM" \
  --reference-rom "$SMS_ROM" --dungeons 5 6 7 8 --frames 60000 \
  --output md/build/v51-recheck
```

CORE is the Genesis Plus GX libretro core, MD_NM the m68k-elf-nm path, and
SMS_ROM the privately supplied original ROM. See ../md/README.md for building.

On 2026-10-08 the workspace had reverted to an older local draft. The exact
published V50 bb49308c9efde72bb2f646109932b451850597a6 was restored first; its
484504-byte BB38 image was reproduced. The older draft remains in a local git
stash and ignored md/build/recovery_20261008/. Work was checkpointed regularly
on work/v51-dungeons before publishing the tested result.
No original ROM, compiled binaries, captures or RAM dumps are committed.
