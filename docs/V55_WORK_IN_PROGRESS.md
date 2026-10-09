# V55 — escape correction and better MD boss arrival, no native pass yet

`evade` clears the unfinished navigation target before evaluating each
candidate and before committing the selected route. An off-grid hero could
previously keep the old walk target for every candidate, producing no escape.
A regression test reproduces this at X=89 with an old rightward target while
the threat is on the right.

The retained travel change targets magic drainers 77/78/82 after curse/grab
actors in dungeons 9/10 only, and only when hero HP <=72. Fire can then use an
8-MP reserve. Native `entity77_wrapper_resource` confirms contact removes
8 MP for those types. Applying this policy at all HP was rejected because
it regresses the previously successful SMS route.

The selective policy preserves the strict original-SMS dungeon-9 pass:
25 visits, one staircase, one key, 90 boss HP removed in 15 real hits,
crystal collection/acknowledgment and overworld return with 124 HP at frame
17286. The escape-only run passes identically. 46 tooling tests pass.

Native MD 9 now arrives at the boss with 70 HP and 8 MP, no potion, versus
18 HP / 16 MP in V54. The default boss controller still dies after four
hits. The optional `--patient-boss` probe waits during moving phases unless
the hero is invulnerable, and uses body margin 6. It reaches 13 genuine hits
(12 boss HP remaining) before dying at frame 49106. Strict native dungeon
validation therefore remains incomplete. The option is explicit; default
SMS boss behavior is preserved. A further timer-aware probe was tested,
regressed native combat to nine hits and was reverted.

SMS 10 still dies at $16A before the boss with the escape-only correction.
The selective-fire change has not been retested through dungeon 10. Resume
with avoiding the remaining type-117 projectile hits in the MD patient probe,
then inspect $18D/$18E backtracks and renewed curse at $13D in dungeon 10.

The original heal routine at $3021 was inspected: it reads environment
$C041 and heals 32 in mode 2, otherwise 16. Native code matches; this is not
a decompilation mismatch. No production C/ROM changes are made. The checked
MD image remains V50, 484504 bytes and checksum BB38. Private ROMs, reports,
binaries and captures stay ignored under md/build/v55_*.

See dungeon_traversal_v55.json for compact outcomes, code hashes and the
patient-probe command; it reports failed attempts as failed, not releases.
