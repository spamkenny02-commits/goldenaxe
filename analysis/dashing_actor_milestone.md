# Dashing actor3C - v0023

ROM: `versions/v0023-3cfc6137/gaw-megadrive-v0023.bin`.
SHA-256: `3cfc61378ff64ecf311163707de88b6f309892e864693bcedcf849f1bb0b04b3`.
v0022 is an intermediate build, retained for version history.

The native dispatcher now translates the original3C states92A0..93F1 to
compiled68000 code. The actor waits for its counter, appears on terrain1F,
uses the source84FA emergence animation, then switches to8BEF and walks at
half a pixel per tick. At walking boundaries it checks obstacles and a random
choice:0/1 selects a direction change,8 selects the dash, and the other values
continue walking. The dash prepares for eight ticks with descriptor8C67,
then switches to8C91 and aims with the original eight93FA vectors and93F2
facing table. Its96-tick counter and common object-tail movement are retained.

Leaving X8..247 or Y8..151, or reaching counter zero, clears display/contact
flags and velocities while preserving the actor record. A source-observed
random113..128 counter precedes reappearance. Spawn can fall through directly
to the walking-selection state if a retained emergence pose is already3;
v0023 also preserves this detail. The extractor exports the original40-byte
facing/vector block and complete terrain table without reinterpretation.

## Verification

Live SMS/native comparisons pass in both NTSC and PAL:

- 32 deterministic state/direction cases.
- 192 source-observed random emergence/walk/dash choices.
- Eleven110-frame trajectories, proving all eight distinct octants, ties and
  the zero vector, through disappearance and the hidden countdown.
- Nine boundary/lifetime cases.
- Two accepted appearance fixtures per region, including the retained-pose
  fallthrough, and four refused terrains.

The state/trajectory suite compares4355 actor records per region,8710 overall.
Only renderer-dependent collision-list bytes27/28 are excluded. Random choices
are explicitly controlled for fixtures at appearance, walking decisions and
the hidden-delay event. This does not reproduce the original R stream.
The trajectory tests collect RAM directly rather than creating video/state
files each frame; these fixtures remain entirely outside the cartridge.

Separate cold-boots of SMS and MD from room9B/9C save checkpoints observe
walking and actual dash state14 over4200 frames per console/room, with no
RAM injection. Random movement/spawn timing remains different. Checkpoints
do not prove natural progression or full combat/pixel equivalence.

Regressions pass for38/39 and their1F shots, four-way scroll visibility in
PAL/NTSC, natural hero/scroll timing and deterministic enemy movement in both
regions, and title cadence/video in both regions. The1F trajectory fixture was
strengthened: the eight previous origins exercised only six distinct octants,
despite earlier descriptions calling them eight octants. Its new origins and
an assertion against the source velocity table now prove all eight distinct
vectors. Earlier archived reports are retained unchanged; their narrower
coverage should be read with this correction.

`dashing_patch_audit.json` binds twelve reports to this exact512KiB cartridge,
checks its checksum/aliases and the supplied SMS ROM, and verifies the actual
cartridge bytes for the dash vectors and terrain table against the source.

## Remaining work

The full game port is unfinished. Types3D onward, dungeon/conditional quest
behavior, original RNG and clock,495E sprite-overflow handling, remaining audio
event coverage, exact intro reveal/startup timing and full-game progression
and rendering verification remain pending.
