# V99: full-entry native ending passes with explicit final-boss HP assistance

At the user's request, a separate cheat-assisted diagnostic completes the
native dungeon10 route from its existing equipped overworld checkpoint,
defeats the actual90HP boss in23 axe hits, shows all nine ending crystals,
finishes the credits and confirms title state12. The run takes89883 frames.
This establishes an assisted full-entry ending path, not an unassisted
completion or a new-game-to-ending equivalence proof.

`--cheat-final-boss-hp` restores living hero HP to its existing maximum
only in gameplay state0C, room14C, while actual boss109 is present.
It writes only C318. It does not freeze invulnerability, suppress damage,
modify boss HP, grant magic or alter progression. Dead heroes are not
resurrected, and the cheat stops during the ending or after boss death.
Every intervention is recorded in `cheats.events`, and console output
identifies the run as `assisted`. The ordinary post-fixture write guard
remains intact; the HP exception uses its own narrowly scoped writer.

The hero reaches14C without assistance at22HP/16MP. Ten HP interventions
follow: the initial22→128 refill and nine damage refills.
The assisted driver's14C visit snapshot records128HP after that first
refill; its intervention event records the prior22HP, also reproduced by
the unassisted control.
The genuine boss hit sequence reaches0HP and exactly one boss death is observed. Ending
handoff occurs at frame80549; the credits finish at89458 and the title
is confirmed before the run stops. No further HP assistance is applied
during the ending.

`validate_assisted` checks the entire ordered entrance route, initial full
boss HP, damage chain, death, all nine crystals, credit scroll and title
confirmation. The ordinary `validate` and `validate_segment` reject enabled
cheats even if no intervention happened. The normal regression wrapper
does not enable the cheat.

A full-entry control with the cheat disabled reproduces V98 exactly:
78099 frames, identical room visits/events and boss phases/hits/deaths,
eleven axe hits leaving46HP on the boss, followed by hero death. Thus the
unassisted full-entry gap remains open. No new SMS result is claimed.

Reproduce the assisted native run from the repository root:

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --combat --dungeon 10 --potion-first --miniboss-spacing \
  --late-shield-first --late-ice --late-live-targets --late-retreat \
  --late-retreat-window 0 --caster-room-retreat --late-terrain-awareness \
  --late-contact-awareness --caster-projectile-awareness \
  --final-magic-reserve 8 --guard-melee-geometry --guard-axe-margin 4 \
  --timed-late-terrain --exit-room-melee-geometry --exit-room-axe-only \
  --boss-projectile-window 0 --boss-projectile-distance 32 \
  --cheat-final-boss-hp --frames 120000 --output md/build/dungeon10-v99-assisted
```

Remove `--cheat-final-boss-hp` for the control, which is expected to fail
completion. The cheat requires dungeon10 and combat recording. This is
an emulator test option, not a retail Game Genie code or a production ROM
change.75 tooling tests, Python compilation and diff checks pass, including
disabled/no-write behavior, exact intervention recording, scope boundaries,
strict rejection and assisted ending validation. Compact evidence and
private-report hashes are in dungeon_progress_v99.json. Production C,
the entrance fixture and the V50 MD image remain unchanged.
