# V97: final dungeon10 arena reached from the overworld entry

During the requested30-minute session, full-entry native dungeon10 advances
from the V94 death in16B to the genuine final-boss arena14C. The best
arrival has20HP/8MP; two axe hits reduce the actual90HP boss to82HP before
the hero dies to three117 projectile hits. The equipped overworld fixture,
production C and V50 image remain unchanged. This is still not a completed
full-entry dungeon or new-game-to-ending proof.

The retained optional guard controller uses original axe/body rectangles
and retreats during enemy hit flash. A4-pixel guard margin leaves26HP after
16B instead of24HP with margin2 in the timed-pit route; the changed outcome
also preserves that health through16C. Timing/drop trajectories differ, so
the result must not be generalized to every seed or hardware platform.

Timed terrain avoidance restores passage through14A's necessary cycling
pit corridor. The raw strict policy clears14A's enemies and keeps46HP but
cannot exit; a24-tick animation forecast allows41 metatiles only when they
stay in that phase over the forecast. The cache optimization reproduces
the uncached run's75620frames/outcome. Prediction is a walking heuristic,
not a guarantee against recoil or every future terrain loss.

The15C dormant-enemy fix now checks actual path reachability instead of
choosing only the closest activation point. A former run stalls forever
at[184,120], pressing toward an unreachable point[184,112] while a dormant
88 waits at[200,96]. The fixed controller tries eight near activation
positions, filters known hazards and chooses a reachable path. It waits
inside the original24x24 proximity square for actual activation. This
clears15C in the new full-entry tests, losing6HP there to88 contacts and
no recorded environment4 damage. One arrives at the boss with10HP; the
larger guard margin improves that to20HP.

Rejected comparisons remain in the compact report archive. Ice against16B
guards consumed necessary MP and was removed. Checked18A shield melee
failed14A and was removed. Applying the general patient policy to mini-boss
123 regressed15E; the final-only patient option is scoped to109. The fixed
SMS timed/guard suffix reaches the boss but fails there, so no new SMS
suffix pass or cross-platform equivalence is claimed for these policies.
V94's previously successful separate equipped suffixes remain valid for
their own recorded options.

Reproduce the20HP native arrival, from the repository root:

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --combat --dungeon 10 --potion-first --miniboss-spacing \
  --late-shield-first --late-ice --late-live-targets --late-retreat \
  --late-retreat-window 0 --caster-room-retreat --late-terrain-awareness \
  --late-contact-awareness --caster-projectile-awareness \
  --final-magic-reserve 8 --guard-melee-geometry --guard-axe-margin 4 \
  --timed-late-terrain --exit-room-melee-geometry --final-boss-patient \
  --boss-projectile-window 8 --boss-projectile-distance 32 \
  --frames 100000 --output md/build/dungeon10-v97
```

The runner correctly fails its completion assertion. Every action after
the existing fixture is joypad input.67 tooling tests, Python compilation
and diff checks pass, including inaccessible activation goals, pit timing,
safe outward exit targets and final-only patient behavior. Session saves
are V95,V96 and this final checkpoint. Completed private-report hashes and
selected policies are recorded in dungeon_progress_v97.json.

The final wider-distance trials (48/64 pixels,16-tick flash window) each
reach the boss but land only one hit before death, so neither improves the
20HP/two-hit result. The next focus is arriving with enough health/magic
and avoiding the final boss's117 projectiles during committed axe swings.
