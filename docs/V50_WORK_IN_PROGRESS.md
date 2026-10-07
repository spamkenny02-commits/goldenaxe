# V50 work in progress

This checkpoint is deliberately on a work branch. Main remains the tested V49.

Validated during the current work:
- Full final boss / ending / credit scroll / nine crystal sprites / confirmation / actual title state 12 on original SMS and native Mega Drive.
- 354 complete merchant purchase/refusal cycles across 23 shops, compared frame by frame to original $7390. Potion shop recognition now uses the original five-cell table.
- 38 fixed item and permanent HP/MP capacity cases, including already collected and inactive conditions, compared frame by frame to original callbacks. Restored capacity dialogue, SBC borrow semantics and HP animation timing.
- 72 full-screen effect cycles with actual selected item 6 at both levels. Corrected damage lookup to selected_item * 4 + level.
- Merchant/item ASan and UBSan checks passed with leak detection disabled (unsupported in this environment).
- Services, player items, boss rewards, combat, ending, transitions, world scroll, native boot and save cycles passed.
- Prepared equipped checkpoint dungeon runs 1-4 reached their boss, crystal and overworld exit on original SMS in pilot runs. Dungeon 1 also passed the strict native MD runner.

Outstanding:
- Dungeon navigation is not yet fully validated. The prepared fixture starts outside a dungeon and forbids RAM writes afterwards; every subsequent action is controller input. Gear acquisition from a fresh game is outside this fixture.
- Dungeon 2 currently stalls outside its entrance on native MD; investigate driver versus production differences.
- Later rooms require deliberate detours between isolated room sections, remote switches, destructive magic and minibosses. Route construction and combat driving remain experimental.
- Latest pilot directories are ignored md/build/v50_pilot23/. Dungeon 5 reached its boss/reward but stalled on the return. Other later dungeon pilots remain incomplete.
- Results, screenshots, work RAM dumps, original ROM data and full binaries remain private ignored build products.

Workspace: /workspace/scratch/61ae24518081/goldenaxe
Original private input: /workspace/scratch/cf0d2e62719b/recovery/Golden Axe Warrior (USA, Europe)(1).sms
Core: /workspace/scratch/cf0d2e62719b/genesis-plus-gx/genesis_plus_gx_libretro.so
Toolchain prefix: /workspace/scratch/cf0d2e62719b/goldenaxe/md/toolchain/bin/m68k-elf-
