# Type67 composite boss: v0112

ROM `versions/v0112-f01b1bee/gaw-megadrive-v0112.bin`, 1 MiB,
SHA-256 `f01b1beee7001aa50e7b71d79fa182106beb0e8906b31d9397fa946e8325db31`,
checksum 7503. Original room list contains type67 in room0179.

## Translation

Native C translates fixed entry5193 and bank2 tableA972, twelve even states
0..22. Core initialization and 112-tick wait, appearance/teleport phases,
nonlethal reaction, reforming, five delayed apparitions, projectile15 firing,
parent-state coordination and 48-tick fade/removal follow the original writes.
Original three five-position tables at AB1C are extracted as thirty bytes.

The initial core places five type67 records in fixed slots1..5 with waits
80/64/48/32/16. These writes preserve unrelated fields exactly like A9AE.
Apparitions read the core formation and their slot, then flash for48 ticks.
They become active with source random wait113..128 (112..127 after same-frame
integration). A nonlethal core hit sets reaction state10 before generic damage,
then state12/14 coordinates apparition fade. State14 schedules replacements.
Parent type7 or state14 makes active apparitions enter state22 and disappear
after48 ticks. Core death proceeds through the existing boss-death/gem chain.

Only source LD A,R choices are supplied by provisional SGDK random() in the
production call sites, sampled when the corresponding branch actually needs
them. No interpreter or captured actor states are used by the production ROM.
Type67 collision descriptors publish after current behavior/flash, as by0940.

## Evidence and limits

- 870 direct original/native cases compare every byte of all sixteen actor
  records. Covers all twelve states, three formations, all five apparition slots,
  selected waits, surviving/lethal pending-damage boundaries, formation/position
  and firing/duration inputs, occupied projectile pools. Five original LD A,R
  sites are replaced only in the fixture with a register-preserving RST30 input
  shim; all other boss instructions/allocator execute unchanged.
- Ten controlled production segments PAL/NTSC total924 frames. Idle, nonlethal
  hit/retreat, death/removal and fade cases compare all768 bytes over584 frames.
  The340 appearance frames compare all other bytes while explicitly allowing
  five apparition random timer fields to differ:264 NTSC and370 PAL differing
  timer samples. Both implementations satisfy initial bounds and decrement by
  one thereafter. Original refresh/RNG equivalence is therefore NOT established.
  Initial records/hero position and pending damage are controlled fixtures in
  an exterior; death cases occupy transient slots after pool clear to isolate
  deterministic behavior from death-particle randomness.
- Actual room0179 entry uses normal dungeon doorway then controlled relocation
  to room0178 boundary, followed by production right-scroll, room scripts and
  resource/actor loading. Forty-seven actor frames aligned to core initialization
  and all24 sprite tiles at three relative frames match in both regions.
  Arrival frame is3440 SMS/3441 MD NTSC and3439 both PAL: absolute NTSC loading
  cadence is one frame late. This test does not prove full transition timing.
- Patch audit reconstructs v0111 actors after removing only type67 additions;
  main.c/second-boss resources unchanged and formation resources exact.
- First boss1789 routines/six production segments, satellite boss1138 routines/
  twelve production segments, ordinary timing PAL/NTSC, six inventory returns
  and two controlled boss-death/gem chains pass on this build.

Captures in `validation/composite-boss-entry-*-*/` show the actual boss room and
five green apparitions. Full SAT/framebuffer/audio equivalence, natural travel
and complete combat remain unproved. Original RNG/refresh, previous scrolling
timing differences, first-boss full-pool IY side effect, other bosses, quests,
ending and full natural playthrough remain unfinished.

Next: types68/69, fixed entry51AE and its shared multi-record behavior.

Reproduce: extract_composite_boss.py; build.ps1;
validate_composite_boss.py --generate; build_composite_boss_harness.ps1;
validate_composite_boss.py; validate_composite_boss_gameplay.py;
validate_composite_boss_entry.py; audit_composite_boss_patch.py.
