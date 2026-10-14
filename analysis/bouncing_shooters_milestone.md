# Walkers38/39 and bouncing projectile1F - v0020

ROM: `versions/v0020-3fcc82be/gaw-megadrive-v0020.bin`.
SHA-256: `3fcc82be4c00617bb36be4e1adfd765e8443daa536afa7b61484c4ff1b434748`.

The native actor dispatcher previously had no behavior for types38/39 or their
projectile1F. The port now translates source states90DB..919A: emergence, random
direction choice, quarter-pixel walking, a sixteen-tick aiming pause, projectile
emission, and the two recovery pauses. Both actor types use this same state
machine with their original room graphics and statistics.

Projectile42B4..4365 now initializes its gravity to-40, aims at the hero using
the original4366 template, copies its ground velocities, and starts each hop
with vertical momentum528. The existing ballistic integrator matches420D:
ground position, gravity, height with negative clamp, and final position.
The ordinary object-tail movement still runs afterwards, as on the SMS.
The projectile checks Y8..159 and X8..247, changes to its reset state when the
height reaches zero, and refreshes its96-tick counter on each hop. Initialization
preserves the fractional ground bytes, and emission preserves unused record
bytes rather than clearing a free slot. A full eight-slot pool drops the shot
while allowing the shooter to continue its recovery, as source4965 does.

The aimed-header and octant logic was factored into a shared native helper;
existing13/14/15/1E behavior uses the same implementation. The extractor adds
the original4366..438B bytes to its projectile-template asset. No emulated
Z80 instruction interpreter or captured gameplay states are linked into the
cartridge; these actor routines execute as compiled68000 code.

## Verification

`validate_bouncing_shooters.py` compares actual live SMS and MD cores, using
test-only initial actor fixtures. In each of NTSC and PAL it verifies:

- 72 deterministic shooter state/direction cases, including the emitted slots.
- 192 original-observed direction/behavior choices, controlling the corresponding
native random choice rather than pretending to reproduce the source R stream.
- Nine transient-pool occupancies, from empty through all eight slots occupied.
- Fourteen boundary, state-entry, fractional-carry and negative-height cases.
- Eight projectile octants followed freely for150 frames, with repeated hops
and all eight eventual culls matching the source.

That is4574 actor-record comparisons per region,9148 total. Only the two
renderer-dependent collision-list descriptor bytes27/28 are excluded.

`validate_bouncing_rooms.py` cold-boots both consoles from save checkpoints in
rooms15 and24, then observes4200 frames of input-driven execution without RAM
mutation. Both types walk and aim in at least one checkpoint, and both consoles
emit1F shots in each room. Absolute spawn/shot timing and random walks differ;
in particular MD type38 does not enter its aiming state during the observed
room24 run, but it does in room15. This test proves active behavior in real
rooms, not identical RNG, full combat equivalence or complete progression.

Regression checks pass for36/37 and their19/1E projectiles, the four scrolling
directions in both regions, natural hero/scroll timing and deterministic enemy
motion in both regions, and title cadence/video in both regions. The title
tests retain their existing startup-offset limitations. Scroll setup/loading
can retain the previously documented one-to-five-frame differences.

`bouncing_patch_audit.json` binds the ten targeted reports to this exact
512KiB cartridge, checks both aliases, its additive checksum and the unchanged
original SMS ROM. Numbered ROMs and archived validation reports remain immutable.

## Still pending

This is an additional enemy-family milestone, not a finished game port.
Types3A onward, dungeon and conditional quest behavior, original RNG/clock,
sprite-overflow handling495E, remaining audio event coverage, exact intro
startup/reveal timing, and full-game progression and rendering verification
remain unfinished. The scrolling fix from v0019 is retained.
