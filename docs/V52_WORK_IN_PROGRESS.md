# V52 — late-dungeon traversal checkpoint (not complete)

V51 on main remains the completed dungeon 5-8 checkpoint. This branch saves
work on dungeon 9/10. Neither late dungeon has passed the strict complete-route
validator at this checkpoint. Production C and the MD image are unchanged:
484504 bytes, checksum BB38, reset 000200.

## Established route correction

Dungeon 9's BC ($B670) switch opens the east gate, not the northern boss gate.
The neighboring BD ($B679) switch sets bit 5 in BC. The generated outbound
route now visits BC -> BD -> BC before AC. Original-SMS pilots traverse this
circuit and enter the real boss room. The route regression is covered by a test.

## Controller work saved for continuation

- Keep the axe selected between late-dungeon approaches, while preserving the
  sword request during grab release. Follow opposing shield facing throughout
  sword AND axe animations for enemies 92/93.
- Delay late-dungeon antidote use until active curse casters are dead. In dungeon
  9, preserve it across FD for the next curse room FE. The fixture still has one
  antidote; inventory consumes it through the original item routine.
- Use the actual 24-MP healing cost in late dungeons and prefer the ordinary full
  heal potion before repeated magic heals.
- Experimental spacing and retreat during boss/miniboss hit invulnerability
  aim to reduce contact damage. These changes have not established a successful
  full late-dungeon run and need further emulator validation.
- Stop failed runs at the first zero-HP frame and include MP, actual/requested
  item, curse and antidote status in progress logs. Failure assertions remain.

34 tooling tests pass. The MD ROM checker passes. Existing V51 combat comparisons
and dungeon 5-8 results remain prior evidence; no production source changed.
The new late-dungeon policies are scoped to indices 9/10.

## Observed limits

Original-SMS dungeon 9 pilots reach the full-HP boss (90 HP) and inflict genuine
6-HP axe hits. They still die before its defeat. The MD pilots reach AC but enter
with too little HP and have not established a boss defeat. Dungeon 10 passes its
123 miniboss in the improved curse pilot and reaches the stair room 14D, but dies
before the remaining circuit. These are partial diagnostic results, not passes.

`dungeon_progress_v52.json` records prototype summaries and hashes of this saved
controller. Reports refer to successive prototypes; they must not be presented
as successful validation of the final saved controller. Current experiments are
under ignored `md/build/v52_*`. Original ROMs, binaries, captures and RAM dumps
are excluded from GitHub. All traversal actions follow a single equipped setup
outside the entrance; no HP/MP/keys or progression are injected during traversal.

Next: reduce contact losses around minibosses and boss 108, complete dungeon 9
on both backends, then complete the dungeon 10 circuit and ending. Use the strict
validator in `tools/test_md_dungeon_emulator.py` before promoting these results.

## Step 2 — axis placement, original-SMS arena passes

The large-boss controller now approaches an axis offset instead of the boss
center, finishes the axe animation before repositioning, and retreats during
hit invulnerability. `--late-boss-controller` exposes the same method in an
isolated real boss 108/109 arena, so it can be diagnosed without replaying travel.

Original-SMS boss 108 (90 HP) passes: 15 genuine 6-HP hits, one death, crystal
collected/acknowledged, 2099 emulator frames. No healing was used: MP remains
120 and the one potion remains available. Hero survives on 44 HP before the
normal reward restores HP to 128. This is equipped ARENA evidence; dungeon 9
is not yet a pass. MD arena and full-route runs are the next checks.
