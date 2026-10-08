# Golden Axe Warrior — SMS decompilation / native Mega Drive port

Faithful decompilation of **Golden Axe Warrior** (Master System) into portable C, with a native Motorola 68000 / Mega Drive backend.

## Current status (V51 checkpoint)

- V51 validates full dungeon 5 and 7 routes on native MD and original SMS,
  including full-HP bosses, crystals, stairs and the outside return. It fixes
  controller navigation costs/cache permissions, intended room-return loops
  and escapes from grabbing enemies. 17 tooling tests and 5004 original-Z80
  combat cases pass. The production image remains V50 (484504 bytes / BB38).
  Dungeon 6 and 8-10 traversal remains open. See `docs/V51_WORK_IN_PROGRESS.md`.

- V50 completes the final boss, credits and confirmed title return on native MD
  and original SMS. It fixes potion-shop recognition, capacity-item dialogue,
  borrow/animation behavior and full-screen magic damage indexing. 354 merchant,
  38 world-item and 144 full-effect differential cycles pass. Dungeon routes
  1-4 pass on MD; later controller routes remain experimental. The native image
  is 484504 bytes. See `docs/CONTINUOUS_V50_PROGRESS.md` for exact scope.
- V49 validates all ten boss fights in their real arenas on MD and SMS,
  starting from controlled equipped checkpoints and driving combat/rewards
  exclusively with joypad input afterwards. All satellites/parts, nine crystal
  rewards and final-boss ending handoff pass; the final boss rejects the sword.
  Tests exposed and fix skipped crystal presentation/healing and truncated,
  misindexed loot data. 18 full reward cycles and 2816 new loot cases match Z80;
  the rebuilt native image is 484500 bytes. See `docs/CONTINUOUS_V49_PROGRESS.md`.
- V48 validates four magic entry points and boss types 99..109 against
  original instructions: 8578 phase/death/projectile cases and 304 item cases
  pass, also under ASan/UBSan. Fixes include boss movement, orbit transitions,
  the real type-103 controller/parts and LFSR attack selection. The native MD
  image builds and combat/save regressions pass; boss fights and magic routes
  through controller input remain open. See `docs/CONTINUOUS_V48_PROGRESS.md`.
- V47 adds controller-only combat against five enemies, checking attacks,
  player/enemy damage, projectiles, deaths and survival. New original-Z80
  tests expose and fix enemy transition, movement-counter and clone-damage
  errors: all 4992 collision/damage/entropy-replayed AI cases pass. The new
  MD route kills two enemies and finishes at HP 16; SMS also passes combat
  checks, with different random trajectories. Native image: 479560 bytes.
  See `docs/CONTINUOUS_V47_PROGRESS.md`.
- V46 adds a controller-only village/save-service route: overworld travel,
  door entry, dialogue and slot-0 save run without work RAM edits. A fresh
  process restores its 592-byte payload and returns to village 94 with HP 24.
  The SMS reference follows the same state/game-counter milestones; all
  49152 settled viewport pixels match after fixed DAC conversion.
  See `docs/CONTINUOUS_V46_PROGRESS.md`.
- V45 validates SRAM-only save/reboot/continue cycles: 12 native host cycles
  cover all three slots, both mapper pages and overwrites. Seven actual MD
  emulator scenarios cover three saves, process restarts, overwrite/reload and
  invalid-signature recovery. The runner imports/exports logical 32 KiB SRAM.
  Service arrival is controlled; production menus use controller input.
  See `docs/CONTINUOUS_V45_PROGRESS.md`.
- V44 fixes a VBlank race between the two SMS video-command bytes, restoring
  the original RST $28 interrupt protection. The 363 differing pixels are
  resolved: the settled route viewport matches all 49152 SMS pixels using
  fixed DAC conversion. All 537 native raster stages / 30793728 pixels pass,
  including a forced-interrupt regression that fails without protection.
  Route cadence stays at 529 gameplay frames; idle measures 225/300 updates.
  See `docs/CONTINUOUS_V44_PROGRESS.md`.
- V43 optimizes sprite collision scratch clearing and opacity merges, plus
  clipped-row mask generation. The controller route uses 529 gameplay frames
  versus V42's 571 (7.4% fewer), with the same final cell/position/HP. Idle
  remains 227 updates/300 frames. All 536 raster stages and the modified
  helper/sanitizer/hardware collision checks pass; its observed full-game screenshot
  regression is resolved by V44. See `docs/CONTINUOUS_V43_PROGRESS.md`.
- V42 restores full-game local validation and caches unchanged physical scroll
  tables, invalidating after the H-scroll line handler and backend reset. All
  536 native raster stages / 30736384 pixels pass locally. The full-game image
  links (478284 bytes, BSS 32296); idle measures 227 updates/300 frames and
  the controller route matches SMS final cell, position and HP. See
  `docs/CONTINUOUS_V42_PROGRESS.md` for measured limits.
- V41 implements rendered eight-sprite-per-line clipping and 2x sprite zoom
  using cached private MD pattern slots. All 532 native raster stages /
  30507008 pixels and the new sanitized helper tests pass in GitHub Actions;
  V41 full-game validation was deferred at that checkpoint.
- V40 corrects the top-edge Y wrap for zoomed sprites, including E0's one
  visible row. All 6951 host cases pass; portable C matches all 1024 status
  values observed by an independent generated Z80 hardware probe.
- V39 remaps the native name plane to preserve SMS's 224-pixel vertical
  wrap. Host tests cover every vertical value and dirty-row rotation; the
  hardware fixture passes 515 stages / 29532160 pixels in GitHub Actions.
- V38 fixes the MD background palette-zero layer while keeping zero pixels
  below sprites. A standalone ROM-free 68000 hardware fixture and pixel oracle
  pass in GitHub Actions: all 172032 rendered pixels match the independent oracle.
  Full-game validation was deferred at that checkpoint.
- 127/127 active entity types are high-level C; no entity Z80 fallback remains.
- 512/512 world callback entries are native/no-op; no world callback fallback remains.
- Map loading, progression, gameplay renderer, HUD, map animation, entity update, gameplay entry, map entity spawning and Arthur initialization are native C.
- Mega Drive backend source and build scripts are present.
- Save initialization `$0404` and initial VDP setup `$03C0` are now native C,
  with differential tests covering 58 SRAM cases and complete VDP state.
- Dialogues, three Yes/No menus, stairs and card-game scripts are native C,
  compared against original RAM, video state and frame timing.
- ROM/video services are separate from the interpreter; cursor effects and item
  graphics loading are native and checked against original execution.
- Pause is native (48 complete modal cycles compared with original execution);
  equipment graphics and pixel remapping are native. Main-state registration is
  now measured explicitly: 12/12 native states.
- All four world effects are native; 72 complete full-screen cycles are
  compared frame by frame with original execution. Scene asset restoration
  also passes 72 full RAM/video/SRAM comparisons.
- Palette fades and the world reveal are native; 48 differential cases verify
  each frame's RAM, VRAM, display registers and final timing.
- New game, continue and scene entry now execute native C: 4,148 complete
  entry comparisons, plus 6,144 map-entity graphics cases across all 512 cells.
- The game-over menu is native, including grayscale fade, checkpoint selection
  and the currency penalty; 128 complete modal cycles match original execution.
- Synchronous IRQ video presentation and its transfer queue are native and
  active every frame; 256 isolated original-block comparisons pass.
- Inventory is native: 432 complete cycles compare all three layers, twelve
  selections, ownership, directional inputs, confirmation and scene restoration
  against original Z80 execution, including every frame and final SRAM.
- Name entry is native: 8,064 cursor/repeat cases, 2,688 edit/confirm cases
  and four full create-name/message cycles match original execution. Longer
  introductory dialogue also exposed and fixed a bitmap-scroll clearing bug.
- Save/shop/inn/upgrade menus are native: 1,024 cursor cases, 25 resource
  drawings and 72 complete modal cycles match original RAM, video, SRAM and
  frame timing. Scene restoration now respects the selected SRAM page.
- The ending is native: four complete final-movement, crystal-reveal and
  credit-scroll sequences match original RAM, video, SRAM and frame timing.
  These comparisons also fixed the missing walk-pose increment.
- V37 reruns every local
  differential/regression target, ASan/UBSan and the compiled native coverage
  gate successfully. Leak detection is disabled locally because this sandbox
  blocks its process inspection; address/undefined-behavior checks remain active.
- Title/intro and new/continue selection are native: 20 complete comparisons
  cover attract mode, scene animations, text, skip paths, saved slots and cancel.
- Boot, name creation, new-game setup and 24 gameplay updates run on the host
  with no interpreter linked. The MD production build also excludes it.
- Screen scrolling is portable C: 220 complete original-instruction comparisons
  cover four directions, three layers, sprite ordering, scratch buffers and
  exact frame timing; 320 cases validate the route puzzle around cell 77.
- Player rotation and five special items are complete portable C: interior
  palette effect, progressive full heal, teleport wipe, terrain transformation
  and the 225-cell overworld map. 48 complete original-instruction comparisons
  check every shared frame's RAM/video/palette/registers, final SRAM and timing.
- V34 moves the sprite-status counters/collision bitmap out of the 68000
  interrupt stack while preserving the V33 Mode 4 calculation. This removes
  roughly 6.3 KiB of automatic frame scratch from the VBlank C call. ROM-free
  oracle validation passes, including the full local sanitizer suite. The
  private-ROM 68000 rebuild and emulator checks now pass in V35.
- Sprite overflow/collision status is calculated from the SMS shadow, with the
  eight-sprites-per-line limit, nontransparent pixels, clipping, 8/16-pixel
  height, zoom and pattern bank. 6,948 independent synthetic scanline/pixel
  comparisons pass, including ASan/UBSan and cached status-latch integration.
  These ROM-free tests run in CI without private cartridge data.
- Bulk VDP transfers preserve scalar address/read-buffer/control-latch behavior
  and exact dirty pattern/name-row/SAT flags. 4,274 ROM-free comparisons pass
  normally and under ASan/UBSan; all original-game differential targets pass.
- The current production image links with GCC 14.2.0: 476,460-byte ROM,
  31,518-byte BSS and checksum BC9D. ELF checks verify mutable state in
  FF0000-FF7B1E, actual IRQ vectors and absence of interpreter
  symbols; cartridge header and checksum checks pass. Genesis Plus GX boots
  through title, name creation, new game and 300 emulator gameplay frames with
  visible graphics and audible PSG. Hardware VBlank and line interrupts are
  connected; asynchronous VBlank continues sound/timers during C computation.
  The V37 idle check advances 239 game updates in 300 physical frames,
  versus V36 148 and V35 136. A bounded dirty-tile iterator and whole-pattern
  three-plane expansion remove the measured per-frame traversal overhead.
  A controller-only route genuinely scrolls from cell 95 to 94 on both native
  MD and original SMS, finishing at position [56,104] with HP 24. MD takes
  508 gameplay physical frames versus V36 721, V35 947 and SMS 348. Performance and a complete
  playthrough/hardware validation remain. Visual comparison exposed incorrect
  background color-zero transparency on MD, which is the next renderer fix.
  Instruction profiling identifies
  shadow VDP writes and physical shadow upload as the main measured costs.

See `docs/CURRENT_STATUS.md` for the exact verified state.

The native registration/completion gate now passes: no instruction bridge calls
or empty Mega Drive presentation hooks remain. All known dispatch entries are
native C. This coverage does not establish complete-game equivalence, a full
playthrough or hardware correctness. Frame-level SMS sprite flags are now
implemented and native sprite clipping/zoom pass generated hardware fixtures;
MD cadence and full-game/physical-hardware behavior
still need validation. The current native image has been rebuilt and exercised
in an emulator, including the first controller-driven screen crossing.
The audio driver passes 144,384 isolated differential updates, including RAM and
ordered PSG/stereo writes, and is integrated into the native IRQ. Sync, async and
line IRQ paths pass 3,072 independent original-instruction comparisons; NMI has
256 cases. Mega Drive IRQ scheduling is active and checked in an emulator. Frame
tests share the native video/input tick; isolated video-block tests compare
the original instructions separately.

## Original game data

This repository does **not** include the original Master System ROM or generated full-ROM dumps. Provide your own legally obtained ROM locally and use the extraction/generation tools in `tools/` for ROM-derived build inputs.

Reference ROM SHA-256 used during reverse engineering:

`852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9`

## Reproduce local validation

From the repository root, with a C11 compiler and Python 3. The video hardware
tests are independent of original game data:

```sh
make test-video-status test-video-status-sanitize test-video-block test-video-block-sanitize test-md-video
```

Reference-game validation requires your original cartridge data:

```sh
make prepare-rom ROM="/absolute/path/to/Golden Axe Warrior.sms"
make test test-final test-reset test-ui test-effects test-assets test-video test-pause test-scene test-full-effects test-transitions test-entry test-map-resources test-game-over test-presentation test-inventory test-menu test-services test-ending test-intro test-audio test-irq test-player-items test-world-scroll test-native-boot audit
make test-sanitize
```

`prepare-rom` accepts only the unheadered 256 KiB reference revision above and
generates ignored `src/original_rom.inc`. An unsupported input leaves any
existing generated file untouched. The other extracted tables are checked in.

`make audit` measures registration through the compiled dispatchers and lists
remaining compatibility calls and empty MD hooks. This completion gate must
eventually pass before claiming a full native port:

```sh
python3 tools/audit_runtime_coverage.py --require-complete
```

It now passes. The probe does not prove all handler states equivalent;
differential and full-game integration validation are still needed.

## GitHub validation and Mega Drive build

Push/PR checks validate extraction failures, portability, backend structure,
ROM-free sprite status (normal and ASan/UBSan) and C syntax without distributing
the original ROM. To enable behavioral tests on
pushes and the manual Mega Drive build, configure the repository Actions secret
`GAW_ROM_BASE64` with a base64 encoding of your reference ROM. It is decoded
privately and its exact SHA-256 is checked before use. Fork/PR jobs do not use
this secret. Without it, CI explicitly reports reference-ROM tests as skipped.

Run **Build Mega Drive ROM** manually after setting the secret. Local builds use
`FETCH_TOOLCHAIN=1 ./md/build_md.sh` or an installed `m68k-elf-` toolchain. A
successful ELF/link/header check will still require emulator and hardware testing;
it does not establish playability. Build artifacts contain game data.

For a sandbox where LeakSanitizer cannot inspect `/proc`, run
`ASAN_OPTIONS=detect_leaks=0 make test-sanitize`; address and undefined-behavior
checks remain enabled. Leak checking is enabled by default elsewhere.

## Goal

The goal is not an approximate rewrite. Gameplay behavior is lifted from the original Z80 program and checked against original execution wherever practical; platform-specific SMS presentation/hardware behavior is isolated behind the platform layer and replaced by a Mega Drive implementation.
