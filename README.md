# Golden Axe Warrior — SMS decompilation / native Mega Drive port

Faithful decompilation of **Golden Axe Warrior** (Master System) into portable C, with a native Motorola 68000 / Mega Drive backend.

## Current status (V35)

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
- V35 restores the private reference/toolchain workspace and reruns every local
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
- The current production image links with GCC 14.2.0: 475,512-byte ROM,
  31,514-byte BSS and checksum D956. ELF checks verify mutable state in
  FF0000-FF7B1A, actual IRQ vectors and absence of interpreter
  symbols; cartridge header and checksum checks pass. Genesis Plus GX boots
  through title, name creation, new game and 300 emulator gameplay frames with
  visible graphics and audible PSG. Hardware VBlank and line interrupts are
  connected; asynchronous VBlank continues sound/timers during C computation.
  The V34/V35 idle check advances 136 game updates in 300 physical frames.
  A controller-only route genuinely scrolls from cell 95 to 94 on both native
  MD and original SMS, finishing at position [56,104] with HP 24. MD takes
  947 gameplay physical frames versus SMS 348. Performance and a complete
  playthrough/hardware validation remain. Instruction profiling identifies
  shadow VDP writes and physical shadow upload as the main measured costs.

See `docs/CURRENT_STATUS.md` for the exact verified state.

The native registration/completion gate now passes: no instruction bridge calls
or empty Mega Drive presentation hooks remain. All known dispatch entries are
native C. This coverage does not establish complete-game equivalence, a full
playthrough or hardware correctness. Frame-level SMS sprite flags are now
implemented; MD cadence, actual sprite clipping and full-game/hardware behavior
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
make test-video-status test-video-status-sanitize test-md-video
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
