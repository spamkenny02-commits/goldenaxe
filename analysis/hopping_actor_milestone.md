# Hopping actor3F - v0025

ROM: `versions/v0025-e95a6b5b/gaw-megadrive-v0025.bin`.
SHA-256: `e95a6b5bfe9f5e1a714f6042531779e8213fcda3ac41cb142b2b7d4f9d005c58`.

Source94B8..963A is now translated to compiled68000 code. Actor3F waits for
its counter, appears on terrain3A, and starts a48-tick emergence using8D6A
and gravity-32. It then selects a direction and walks using85EA, an eight-tick
step with one-pixel velocity. At the end of a step, random0/1 changes direction,
random8 starts its hopping preparation, and the other choices continue walking.

Preparation stops ordinary velocity, saves the high bytes of ground position
while retaining fractions, initializes a four-hop budget, and waits16 ticks.
Each hop chooses one of the original8CA3 vectors. Shadow-ground bounds reject
outward choices, and terrain flags20/40/80 reject blocked landings. A rejected
choice retains the state and fields, allowing another attempt. An accepted
choice initializes vertical momentum528 and uses the existing source420D
ballistic integration. Each landing decrements the four-hop budget. After the
fourth, the actor restores8D6A for48 ticks, clears only its display bit, and
waits a random112..127 counter before appearing again. Ordinary object-tail
movement, counter decrements and retained fields match the source.

## Verification

Live SMS/native comparisons pass in PAL and NTSC:

- 36 deterministic state/direction/height-underflow cases.
- 384 source-observed emergence, walking, hop-selection and retreat choices.
- 128 source-observed shadow-boundary and terrain landing-guard cases.
- A complete four-hop cycle, all intermediate ballistic ticks, the48-tick
  retreat and32 further hidden-counter ticks.
- One accepted terrain3A appearance and four refused terrains per region.

The original-observed random choices and spawn IRQ phase are explicitly
controlled in test fixtures. Other ticks evolve freely. The initial192-case
PAL decision sample did not exercise the rare jump-start branch; the retained
384-case suite varies the sampling pattern and asserts all three walking
outcomes. No captured emulator state or fixture is linked into the ROM.
Only renderer-dependent collision-list bytes27/28 are excluded from direct
actor-record comparisons.

Cold-boots from roomDA/FC save checkpoints additionally show3F walking and
actual hop state12 during4200 frames per console/room, without RAM injection.
Checkpoint runs demonstrate activity, not identical RNG or natural progression.

Targeted regressions pass for3D/3E and1A, four-direction scroll visibility in
both regions, natural hero/scroll timing and deterministic enemy movement in
both regions, and title cadence/video in both regions. The previous intro-start
and controlled transition-setup timing differences remain.

`hopping_patch_audit.json` binds twelve reports to the exact512KiB cartridge,
checks its checksum and aliases, verifies the supplied SMS ROM is unchanged,
and compares the compiled hop/walk-vector bytes directly to the source.
The numbered ROM and reports are archived alongside all earlier versions.

## Unfinished scope

Types40 onward, dungeon/conditional quests, source RNG/clock,495E firing
suppression on SMS sprite overflow, remaining audio event coverage, exact intro
reveal/startup timing, full progression and full rendering/combat verification
remain unfinished. This milestone does not establish a complete game port.
