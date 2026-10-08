# V52 — saved late-dungeon checkpoint; full routes remain open

The boss-108 axis controller passes isolated real-arena tests on original SMS
and native MD. Full dungeon 9 and 10 traversal remains incomplete. V51 on main
remains the validated dungeon 5-8 checkpoint. Production C and the MD ROM are
unchanged: 484504 bytes, checksum BB38, reset 000200.

## Route and controller changes retained

- BC ($B670) opens its east gate. BD ($B679) sets BC's north gate bit. Dungeon 9
  now visits BC -> BD -> BC before AC. Pilots reach the real boss on both backends.
- Late-dungeon melee keeps the axe between approaches and follows the opposing
  facing of shield enemies 92/93 during sword AND axe animation.
- Cure waits until active curse casters are dead. In dungeon 9 the single antidote
  is preserved through FD for FE. Real inventory routines consume it.
- Late-dungeon healing uses its actual 24-MP cost. Magic-heal priority is restored;
  the potion-first experiment worsened full-route survival and is discarded.
- Miniboss invulnerability retreat is retained only for dungeon 10. A preceding
  original-SMS pilot reached 16A, beyond the former 14D stop. Dungeon 9 keeps the
  approach that reached its boss with more HP.
- The large-boss controller approaches reachable axis offsets, completes its axe
  swing before repositioning and retreats during hit invulnerability.
  `--late-boss-controller` tests the same method in an isolated 108/109 arena.
  Right-side-only and projectile-evasion prototypes are discarded: they did not
  establish a full-route pass and increased resource use in the arena.
- Failed dungeon runs stop at the first zero-HP frame. Progress logs include MP,
  actual/requested item, curse and antidote state. Failure assertions remain.

## Completed isolated checks

| Backend | Boss HP | Genuine hits | Deaths | Frames | HP before boss death | Potion remaining | MP remaining |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Original SMS | 90 | 15 | 1 | 2099 | 44 | 1 | 120 |
| Native MD | 90 | 15 | 1 | 5757 | 74 | 0 | 120 |

Both collect and acknowledge the crystal. The normal reward restores HP to 128.
The SMS run uses no healing. The MD run consumes its one ordinary potion through
inventory; it uses no MP. `boss.heals` records incremental HP increases during
healing/reward animations and must NOT be interpreted as a count of potion uses.
These are equipped ARENA proofs, not complete dungeon-traversal proofs.

34 tooling regressions pass, including axis placement, swing completion,
invulnerability retreat and BC/BD gate ordering. The MD ROM checker passes.
V51's 5052 original-instruction combat comparisons and full dungeon 5-8 results
remain prior evidence; production source did not change in this checkpoint.

## Exact stopping points and next work

The retained full dungeon-9 controller reaches the boss on SMS and MD, but dies
before victory: 6 hits on SMS (54 HP left), 1 hit on MD (84 HP left). Resource loss
on the route remains the limiting issue. The dungeon-10 mini-retreat pilot reaches
16A after the stairs through 14D/13D/13E, then dies. Its remaining circuit and full
ending are unvalidated. Do not promote these results as a completed V52 release.

Next: reduce losses during travel and preserve healing for boss 108, validate the
entire dungeon 9 with `tools/test_md_dungeon_emulator.py` on both backends, then
finish dungeon 10's circuit and ending. Do not relax the strict validator.

`dungeon_progress_v52.json` stores arena summaries, failed prototype stops and
current script hashes. Diagnostic runs represent successive prototypes; they are
not interchangeable evidence for the saved controller. Current full dungeon-9
reports are `md/build/v52_axis_heal9/` and `md/build/v52_axis_heal9_md/`; arena
reports are `md/build/v52_axis_arena108/` and `md/build/v52_axis_arena108_md/`.
All reports, binaries, original ROMs, captures and RAM dumps stay ignored.

Traversal starts from one equipped setup outside the entrance (128 HP/MP,
20 keys, one potion and one antidote). Afterwards only controller inputs operate
the game. No health, resources or progression are injected during traversal.
