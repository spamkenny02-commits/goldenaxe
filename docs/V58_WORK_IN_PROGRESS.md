# V58 — avoid the second dungeon-10 curse

The controller uses checked axe-2 collision rectangles against type83 in
dungeon10 when fewer than16MP remain and no free fire shot is available.
It swings at safe reach and retreats from a close caster while that caster
is invulnerable. It does not change game RAM or production C. Dungeon9
and other enemy types retain the previous controller.

With the retained change, SMS10 reaches $18A with22HP and no curse, then
dies at frame25505. The earlier retained controller died at $16A. Native
MD10 reaches $13E with110HP and no curse, clears its enemies, but exhausts
magic and times out at90000frames with82HP. Its stair passage needs magic
to clear a blocking tile. Avoiding curse does not complete this route.

A second experiment reserved the last fire cast and added axe spacing
against drainers77/78/82. SMS produces the same failure as above; MD again
stalls at $13E with82HP and0MP. These additional changes are reverted.
The emulator report now records curse transitions, remaining antidotes,
hero state/position/defense and caster snapshots for subsequent diagnosis.

512 new differential cases execute the unaccelerated original $4FF3
wrapper: states8/10, motion phases0/1, four directions, eight contact-flag
values and curse0/1/2/255. All compared game RAM matches native C with
original refresh entropy replayed. The combat suite passes8204cases and
48 tooling tests pass, including safe attack/retreat controller coverage.
No production C change or ROM rebuild is required.

The $17B south entry, $17C remote switch and later stairs still await a
successful full-entry integration run. Native9 and full10 remain open.
Private ROMs, binaries, captures and RAM reports stay untracked. See
dungeon_traversal_v58.json for failed attempts, curse observations and hashes.
