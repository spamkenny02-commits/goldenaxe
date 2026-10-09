# V61 — preserve pre-damage geometry for controller diagnosis

The shield approach experiment plans toward the side accepted by the
original direction gate, swings only at checked axe reach, and retreats
while the enemy is invulnerable. It was tested through joypad inputs only
from the ordinary equipped entrance fixture. It does not improve traversal:
SMS10 dies in14D at14350frames; native10 with potion-first dies in16A at
54830frames. The generalized experiment is rejected.

A second trial limits it to18A and tracks the selected shield during its
swing instead of selecting whichever shield is nearest. Both prefixes
then match the retained route: SMS reaches18A with22HP/0MP; native reaches
it with28HP/8MP. They still die in18A at25467/61540frames respectively.
The controller method, CLI probe and experimental tests are all removed.
The checked V60 driver and optional V59 potion-first are retained unchanged.
No shield-approach improvement or completed dungeon10 is claimed.

The new observations exposed a diagnostic limitation: room-entry snapshots
can precede actor initialization, leaving zero coordinates and hitboxes.
Also, the player position recorded when HP falls is after that update and
may already include recoil. These positions must not be treated as the
exact collision-time geometry.

The runner now additionally records a room snapshot once the hero and at
least one enemy have an active source hitbox. Player-damage entries keep
the previous-frame hero position, direction, defense and source hitbox,
alongside the previously sampled attacker's target box. The post-update
positions remain available. These read-only samples improve reconstruction;
they are not an exact instruction-level trace within the game frame.

48 tooling tests pass and the runner compiles as Python. Production C,
ROM, route data and controller decisions are unchanged. The prior V60
combat suite passed9228cases; it was not rerun for these diagnostic edits.
Full native9 and full10 remain open. Private original ROMs, binaries,
screenshots and RAM dumps stay untracked. See the compact JSON for failed
experiments and report hashes.

A fresh retained native10 potion-first run reproduces V59 exactly: death
in18A at61782frames. The diagnostic output contains active-actor snapshots
and four18A damage events. The room snapshot still contains some actors
in initialization; it is deliberately not a claim that every actor is ready.
The four damage sources are type90, type93, type93 and type90. No projectile
is the recorded attacker in this retained18A failure. Pre-frame samples and
post-update positions are saved together in the compact JSON report.
