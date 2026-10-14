# Pursuit shooters3D/3E and projectile1A - v0024

ROM: `versions/v0024-92b10d8d/gaw-megadrive-v0024.bin`.
SHA-256: `92b10d8d94327cafb570d9e00e0f9050de69d53a89e990c9e12676348029a471`.

Native68000 behavior now covers source9426..94A7 for types3D/3E. Their initial
state reuses the original8530 emergence path. Afterwards they use descriptor
8CAA, ten-tick animation and source85D9 half-pixel walking steps. At a walking
boundary, an obstacle selects a new direction; a random choice can continue
walking or try to align with the hero. Successful row/column alignment performs
a second obstacle check in the new direction, then starts one step in state10.
When that step finishes, a blocked direction or random0..3 returns to selection;
otherwise the actor emits1A and resumes normal walking. The source's field
retention and common-tail counter/movement order are preserved.

Projectile1A uses source408E, header/directional vectors409B..40B0, and the
shared3DAF initialization and3DFA exterior bounds. It retains its128-tick
counter, fixed-point cardinal velocities, animation fields and reflection
flags. The asset extractor appends the original22-byte template; the cartridge
audit verifies those actual compiled bytes against the SMS ROM.

## Verification

Live SMS/native comparisons pass in both NTSC and PAL:

- 32 deterministic shooter state/direction cases.
- 48 blocked-terrain cases using source flags20 and80.
- 192 source-observed choices covering direction selection, continuation,
  alignment, pursuit and firing, including emitted transient records.
- Four independently initialized1A shots followed freely for132 frames,
  including their original boundary culls.

There are3760 actor-record comparisons per region,7520 overall, excluding only
the renderer-dependent collision-list bytes27/28. Native random choices are
controlled explicitly for the deterministic comparisons. Decision fixtures
also clear original C01B's sprite-overflow status; see the limitation below.
All actor fixtures remain outside the cartridge.

Separate cold-boot save checkpoints in rooms26 andBB show3D/3E walking,
pursuing and emitting1A shots over4200 frames per console/room without RAM
injection. Both types enter state10 in at least one checkpoint and both
consoles emit shots in each room. This does not prove identical random walks,
natural progression or full combat/pixel equivalence.

Targeted regressions pass for3C trajectories, four-direction scroll visibility
in both regions, natural hero/scroll timing and deterministic enemy movement
in both regions, and title cadence/video in both regions. Previously recorded
intro-start and controlled transition-setup differences remain.

`pursuit_patch_audit.json` binds ten reports to this512KiB cartridge, checks
its additive checksum and aliases, and verifies that the supplied SMS ROM is
unchanged. v0024 and its reports are archived beside all earlier numbered ROMs.

## Remaining fidelity gap and unfinished scope

Source949B calls495E, which suppresses firing when C01B bit6 reports SMS
sprite overflow. The native helper still allocates the first free transient
record without this suppression. The state-machine/timing tests deliberately
clear that signal rather than silently treating the two paths as equivalent.
Natural room checkpoints demonstrate activity but do not validate this gate.
This is an existing global firing-helper gap, also relevant to earlier actors;
it remains to implement and verify against SMS sprite evaluation.

The game port is still unfinished: types3F onward, dungeon/conditional quests,
source RNG/clock, remaining audio events, exact intro reveal/startup timing,
full-game progression and full rendering/combat verification remain pending.
