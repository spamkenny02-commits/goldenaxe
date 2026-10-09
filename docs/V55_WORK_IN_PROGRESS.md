# V55 — escape search fixed, traversal remains incomplete

`evade` now clears the unfinished navigation target before evaluating each
candidate and before committing the selected route. Previously an off-grid
hero could keep the old walk target for every candidate; no escape would be
recognized. A regression test reproduces this with X=89 and an old rightward
target while the threat is on the right. 44 tooling tests pass.

The saved change preserves the strict original-SMS dungeon-9 pass:
25 room visits, one stair, 15 genuine boss hits, crystal/reward acknowledgment
and overworld return with 124 HP at frame 17286. MD 9 and SMS 10 retain their
V54 blockers; the controller fix is valid but did not solve those scenarios.

Two tactical experiments were not retained. Prioritizing types 77/78/82
and allowing fire below the usual reserve gives MD 70 HP at boss arrival
and four hits before death; it regresses SMS to two hits before death.
The resource-drain behavior is in native `entity77_wrapper_resource` and
applies to 77, 78 and 82. A stationary-boss swing policy plus conditional
anti-drainer fire regresses SMS to seven hits; the MD result is pending.
Only the escape-planning correction is in the saved controller.

The original healing routine at $3021 was checked: it reads environment
$C041 and heals 32 in mode 2, otherwise 16. The native implementation matches;
this is not a discovered decompilation mismatch. No production C/ROM changes
are made. The checked MD image remains V50, 484504 bytes and checksum BB38.

Continue by testing selective anti-drainer fire without changing the proven
SMS boss policy. Any controller variation must retain strict full-HP boss,
room-order, reward and survival checks. Private reports remain in ignored
md/build/v55_*; no original ROM or capture is published.
