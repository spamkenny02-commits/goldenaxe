# V50 work in progress

This file records the experimental dungeon controller work alongside the V50 production fixes.
The fixes and completed ending are validated; full dungeon route coverage remains incomplete.

Validated during the current work:
- Full final boss / ending / credit scroll / nine crystal sprites / confirmation / actual title state 12 on original SMS and native Mega Drive.
- 354 complete merchant purchase/refusal cycles across 23 shops, compared frame by frame to original $7390. Potion shop recognition now uses the original five-cell table.
- 38 fixed item and permanent HP/MP capacity cases, including already collected and inactive conditions, compared frame by frame to original callbacks. Restored capacity dialogue, SBC borrow semantics and HP animation timing.
- 144 full-screen effect cycles retaining selected item 1 and adding actual selected item 6 at both levels. Corrected damage lookup to selected_item * 4 + level.
- Merchant/item ASan and UBSan checks passed with leak detection disabled (unsupported in this environment).
- Services, player items, boss rewards, combat, ending, transitions, world scroll, native boot and save cycles passed.
- Prepared equipped checkpoint dungeon runs 1-4 reached their boss, crystal and overworld exit on original SMS in pilot runs. Dungeons 1-4 also passed the strict native MD runner. Dungeons 5, 6 and 7 completed their SMS pilot runs. Dungeon 6 passed strict validation (42 visits, 3 stairs, 8 full-HP boss hits).

Outstanding:
- Dungeon navigation is not yet fully validated. The prepared fixture starts outside a dungeon and forbids RAM writes afterwards; every subsequent action is controller input. Gear acquisition from a fresh game is outside this fixture.
- Dungeon 2 native entry now passes after restricting destructive navigation to interior rooms. Boss 7 required a closer axe approach in the controller driver.
- Later rooms require deliberate detours between isolated room sections, remote switches, destructive magic and minibosses. Route construction and combat driving remain experimental.
- Latest resumed pilot directories are ignored md/build/v50_resume*/. MD 5/6 pilots remain incomplete. SMS 8 requires remote switches via the 1C8 stairs and 1EB/1EC. SMS 9/10 combat/retreat handling remains incomplete.
- The current equipped fixture uses HP/MP 128, 20 keys, level-2 spells/healing and one apple. Item F0 is enabled for 6/9. These are prepared integration checkpoints, not gear acquisition runs.
- Driver changes include weighted navigation to conserve destructive magic, aiming before casting, six-direction grab release, retreat recovery and MP traces. All are controller inputs; post-preparation RAM writes are forbidden.
- Eleven Python tooling tests pass, including rejection of missing rooms, reduced boss HP, missing hit chains and unacknowledged rewards.
- Results, screenshots, work RAM dumps, original ROM data and full binaries remain private ignored build products.

Workspace: /workspace/scratch/61ae24518081/goldenaxe
Original private input: /workspace/scratch/cf0d2e62719b/recovery/Golden Axe Warrior (USA, Europe)(1).sms
Core: /workspace/scratch/cf0d2e62719b/genesis-plus-gx/genesis_plus_gx_libretro.so
Toolchain prefix: /workspace/scratch/cf0d2e62719b/goldenaxe/md/toolchain/bin/m68k-elf-
