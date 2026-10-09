# V62 — dungeon10 controller trials and bounded emulator output

Dungeon10 is **not complete**. Eighteen full-entry controller trials were
run against the private original SMS ROM or the existing native MD build.
The strict traversal validator rejects all eighteen. The compact JSON
records their frame counts, final rooms/resources and private report hashes.
No production C or route data changes are included.

The following experiments are rejected and removed from the controller:

- Contact-aware axe reach, shield flanking, grouped hazard retreat, and
  prioritizing vulnerable enemies still die in18A on both platforms.
- A patient approach below the type123 mini-boss regresses both runs to15E.
- Seeking nearby mode2 terrain for healing reproduces the baseline failures
  in18A. The original healing action gives32HP in mode2 and16HP otherwise;
  this fact alone does not establish a safe, useful healing detour.
- Giving the original C0F0 equipment flag in the one-time entrance fixture
  allows water walking but regresses native10 to16A and SMS10 to13D. These
  two trials use stronger equipment than the ordinary dungeon10 fixture;
  they are not comparable successes or full-route proof.
- Lowering ordinary fire reserves to64 causes earlier deaths (native14D,
  SMS15E). Native reserve32 dies in18A; reserve8 stalls in13E with28HP and
  no magic through240000frames. Allowing low-reserve fire only against the
  type123 mini-boss also fails (native18A, SMS14D).

The V61 controller and optional V59 potion-first remain unchanged. Native
potion-first still has the documented baseline failure in18A with28HP/8MP
on arrival. Traversal beyond18A, including the17C switch and final approach,
remains unverified from the ordinary entry fixture. The previously isolated
final boss/ending proof does not close that gap. Full native9 also remains open.

The only retained runner change is a bounded console summary. Previously
`print(result)` emitted every combat event at the end of a run, producing
very large log lines. Full observations still go to `result.json` before
assertions; the console now reports frames, location, health, stage, counts,
ending flags and the report path. This does not change game inputs, RAM,
validation or report contents, and is not a claim to fix transport failures.

50 tooling tests pass. New tests check that a large trace is summarized
without mutation, remains bounded, and also supports runs without combat.
Python compilation passes. A10000frame native dungeon10 smoke run checks the real runner output.
Its deliberate frame limit must fail the unchanged completion assertion;
it is not a traversal success.
Unchanged production combat suites are not rerun for this output-only edit.
Private ROMs, binaries, screenshots and raw emulator observations remain
untracked. The next useful work is to reduce actual combat losses while
preserving the strict full-entry proof, rather than widening the fixture.
