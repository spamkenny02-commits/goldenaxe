# Bosses6D and63: v0118

ROM `versions/v0118-a72eb3e8/gaw-megadrive-v0118.bin`,1 MiB,
SHA-256 `a72eb3e83e49733761e285e3639ef6c4a344995fd8fd45f7372b3be8d2c60405`,
checksumD029. v0117 is an intermediate6D-only build; use v0118.

## Type6D55F1 in room014C

Source stats5A200840:HP90,attack32,defense8,flags40. Ten-state table560A
translated. Initialization/recovery sets(128,72),descriptor9E28,64-tick flash,
but deliberately does not initialize animation periods/counts or contact flag.
After flash completion, state2 falls through descriptor/animation reset and
pursuit in the same call. Pursuit targets byte-wrapped(heroY-16), uses577F
asymmetric bounds and55D0 quarter-pixel vectors, with64-tick segments.

At the end of a segment, velocity clears and a conditional random nibble selects
satellite preparation, three-shot attack when the hero is sufficiently below,
or pursuit. The three-shot branch waits32 ticks, animates18, then fires75.
Following intervals wait20 then animate18; the third shot enters state18, which
waits for every transient record to disappear before returning to pursuit.
State10 intentionally retains its prior animation index, unlike type6C.

Satellite preparation/state16 and pool wait/state18 use the already-translated
shared572B/5761 routines. Four76 satellites and75 projectiles retain the v0116
path/homing/bounce/return implementations unchanged.

The55F8 filter runs after every state routine and before generic hurt: pending
damage is retained only when selected item is1 AND its level is2. Native main
exposes exactly that equipment predicate; the actor wrapper clears pending
damage for other choices, including higher levels. Frozen-actor behavior is not
changed. Original random/refresh stream and global clock remain incomplete.

## Type63506B in room0144

Source stats1E080240:HP30,attack8,defense2,flags40;49 loaded graphic tiles.
Dispatch table2B63 maps63 and64 to the same506B/A754 routine. The shared source
checks type64 before sampling the additional random choice for five-shot fan.
Type63 therefore only selects the three aimed72 shots. Added63 dispatch and
conditioned both the choice sample and fan branch on type64. Other first-boss
movement/attack states and projectile routines remain unchanged.

## Evidence

- 482 original/native6D routine cases compare all768 actor bytes. All ten states,
  selected item/level matrix, heroY-16 wrapping, chase bounds, choice gates,
  shot countdown, animation retention, partial/full allocations and pool wait.
  Two LD A,R sites use explicit register-preserving fixture inputs; other
  original instructions execute. Full pools supply ROM IY8000; arbitrary
  inherited RAM IY effects remain unsupported.
- 1789 original/native63-related cases:1320 boss cases and469 shared projectile
  cases. Includes forced state10/fan even though normal63 does not select it;
  this tests shared table entries, not an additional natural attack. Gate/choice
  combinations verify normal63 never selects fan. Original R stream unproved.
- 24 controlled6D production segments,1790 compared frames, all768 actor bytes
  exact in PAL/NTSC. Appearance, pursuit, complete three-shot cycle through pool
  clearance/first pursuit tick, three rejected equipment/damage combinations,
  surviving/lethal pending damage, four explicitly selected satellite formations.
  Hero health/cap128, equipment and records injected in exterior; native clock
  aligned to source. Damage fixtures are pending damage, not natural weapon hits.
  Random choices after the compared cycle prefix are outside this comparison.
- Four63 production segments,244 actor frames exact:appearance/movement and
  aimed-shot segment in both regions, stopping before random decisions. No
  clock alignment injection in these short63 fixtures; full global timing is
  nevertheless not established.
- Four actual destination entries after controlled neighbor relocation:47
  relative actor frames each;121 loaded tiles for6D and49 for63, at three samples per
  region; six18-part6D SAT lists and six15-part63 lists exact (198 entries).
  Entry SMS/MD:014C3448/3449 NTSC,3445/3446 PAL;01443459/3460 NTSC,3455/3455 PAL.
  These relative samples do not prove whole transition/framebuffer equality.
- Scope audit reconstructs v0116 after removing only6D additions,63 shared
  dispatch/choice condition/collision publication and the equipment accessor.
  Existing projectile/satellite routines, renderer and resource tables unchanged.
- Regressions against v0118:first-boss1789 routines/308 frames; satellite1138,
  composite870,charging796,burst974 and6C660 direct cases;6C1518 and burst1008
  controlled aligned frames;6C entry/18-part sprites; ordinary PAL/NTSC timing,
  six merchant/exterior menu returns and two boss-death/gem chains pass.
- Unaligned NTSC contact still reproduces MD2977/SMS2978 and post-frame clock
  difference73 modulo256. This actual timing discrepancy remains unresolved.

## Remaining work

The room-list/dispatch audit found29 loaded actor types46..62 with exported
resources and stats but no native behavior branch. See pending_actor_types.md
and pending_actor_types_report.json. Native resource loading must not be treated
as completion of those enemies. The audit is a reviewed range, not proof that
all other game behavior is complete.

Next: these dungeon actor families, original clock/refresh/RNG, complete audio,
ending, quests/progression/save routes and a complete natural playthrough.
Natural fights and ending are not established by the controlled boss fixtures.
The full port remains incomplete.
