# V95: full-entry dungeon10 reaches the final boss

The best new full-entry native probe reaches14C, starts the real90HP boss109
and lands two4HP axe hits before dying at78276frames. This uses the V94
reserve8/retreat0/controller policy plus checked guard melee in16B; terrain
awareness in this particular run applies to14A only. The unchanged fixture
still starts outside, and the runner permits only joypad input afterwards.
It is not a completed dungeon or new-game-to-ending proof.

Guard melee uses original axe/body rectangles, a2-pixel margin and retreat
from flashing69/73 actors. That run clears16B without health loss, collects
real8MP loot, enters16C with10HP/16MP and reaches15C with the same resources.
In15C real magic loot allows one24MP/16HP heal; contacts/pit damage leave
only2HP at the boss. Ice in16B and ice plus checked melee both reach15C but
spend the magic reserve and die there; the ice probe was removed.

An initial15C checked-melee probe remains stalled at100000frames/24HP
because dormant88 actors require proximity within24 on both axes. The new
probe approaches diagonally and waits for actual activation. Its first run
still dies15C: two4HP losses have environment mode4, with stale attacker
attribution. Pit-awareness now optionally covers15C as well as14A and the
activation approach avoids known cycling-pit goals. That alone does not
prevent every terrain loss; more comparisons remain in progress.

The general patient-boss option changes mini-boss123 timing and causes an
unrelated early death in15E. A separate optional final-boss-only patient
policy now affects109, retaining the earlier route behavior. Checked shield
melee in18A is being tested to conserve health and healing magic before13C.
These are optional controller experiments, disabled by default; production
C and the V50 image are unchanged. Do not promote an unfinished route.

64 tooling tests pass, including dormant-enemy activation near a safe floor
and the existing contact/pit/cache/boss/navigation tests. Diff checks and
Python compilation pass. Private report hashes and actual selected policies
are in dungeon_progress_v95.json. V94 suffix ending proofs remain separate
from full-entry evidence. This is the first10-minute session checkpoint;
shield, pit-only and final-boss comparisons are still running.
