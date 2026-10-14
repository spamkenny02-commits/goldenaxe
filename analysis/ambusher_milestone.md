# Actors40/41, projectile1B and lob1D - v0026

ROM: `versions/v0026-e0fef3c2/gaw-megadrive-v0026.bin`.
SHA-256: `e0fef3c26202309e88b6dcb60217ddc6727d4f9a85daf7ef989f25149d454f7e`.

Source9647..96C0 now executes as native68000 behavior for40. It shares the
walking/pursuit structure of3D/3E but uses descriptor8DB2, random thresholds
2/8, and always attempts a1B shot after an unobstructed pursuit step. The
3D/3E branch retains its original4/10 thresholds and separate firing choice.
Projectile1B uses40CB's original22-byte template and the shared exterior
bounds. On subsequent ticks it also reads the terrain attribute at
(X,Y-4), as source230E does, and clears on flag80. Initialization does not
perform this terrain test, matching the source40B1 branch.

Source96C7..9725 now controls41. It attempts terrain3F placement without a
counter guard, hides, waits a random112..127 counter, reveals for ten ticks,
then hides and allocates two1D records with directions1 then0. Both successful
allocations produce a new random delay. If either allocation fails, the actor
still returns to state0 but leaves its zero counter unchanged. The native
port preserves that partial-allocation behavior rather than forcing an
all-or-nothing shot pair.

Lob1D translates4191..420B, using the two original4277 vectors. It retains
ground fractions, starts momentum512 with gravity-16, and uses shared420D
ballistic integration. Landing clears the record. No new lifetime/boundary
rule is added. Existing stale counter/ordinary-velocity fields are retained,
so the common object tail can still apply its source movement.

## Verification

Live SMS/native comparisons pass in PAL and NTSC:

- For40:16 deterministic cases,24 blocked-terrain cases,192 source-observed
  decisions/emissions, and four132-frame1B trajectories through their culls.
- For41:16 deterministic cases, nine pool occupancies including one/no free
  slot, and four100-frame1D trajectories through landing.
- Ten terrain fixtures distinguish1B's flag80 cull from1A's retained behavior.
- An accepted41 spawn with three controlled random choices (cell, direction,
  hidden delay) and four refused terrains per region. The initial counter3
  explicitly verifies the source's absence of a spawn counter guard.

There are8564 new actor-record comparisons across the two regions. Only
renderer-dependent collision-list bytes27/28 are excluded. The three-choice
spawn fixture selects an observed original event representable by the native
test RNG; this is explicit choice control, not source-RNG reproduction.

Cold-boot save checkpoints in roomsDB/1B show both actors active and emitting
their respective shots during4200 frames per console/room, without RAM
injection. These tests do not establish full natural progression, identical
random walks or complete combat/pixel equivalence.

Regressions pass for3D/3E and1A after the shared pursuit changes,3F's complete
hopping cycle, four-way scroll visibility in PAL/NTSC, natural hero/scroll
timing and deterministic enemy movement in both regions, and title cadence
and sampled video in both regions. Previously documented intro-start and
controlled transition-setup timing differences remain.

`ambusher_patch_audit.json` binds fifteen reports to this512KiB cartridge,
checks the checksum/aliases and supplied SMS ROM, and verifies the compiled
1B and1D vector/template bytes against the source. All numbered ROMs and
archived evidence remain available.

## Remaining scope

40 still uses the globally incomplete firing helper: source495E suppresses
shots on SMS sprite overflow, whereas the native helper does not yet do so.
40 decision fixtures explicitly clear the original status for comparison.
41 calls4965 directly and does not use that gate; its allocation path is
tested without an overflow assumption.

42 remains to translate:9730..983E drives an expanding sinusoidal path and
attacks with1C. Source40E1..4181 initializes that shot, re-aims in sixteen-tick
segments, and stops after eight segments or at exterior bounds. Its headers,
vectors and state transitions have been located but are not yet native code.

The full game port remains unfinished: dungeon/conditional quests, source
RNG/clock, remaining audio event coverage, exact intro reveal/startup timing,
full progression and full rendering/combat verification are still pending.
