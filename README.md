# Golden Axe Warrior — SMS decompilation / native Mega Drive port

Faithful decompilation of **Golden Axe Warrior** (Master System) into portable C, with a native Motorola 68000 / Mega Drive backend.

## Current status (V26)

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
- Strict C11 tests, differential/regression tests, ASan/UBSan and the 68000 portability audit pass on the current working tree.
- Title/intro and new/continue selection are native: 20 complete comparisons
  cover attract mode, scene animations, text, skip paths, saved slots and cancel.
- Boot, name creation, new-game setup and 24 gameplay updates run on the host
  with no interpreter linked. The MD production build also excludes it.
- The 68000 image links with GCC 14.2.0: 427,470-byte ROM, 25,148-byte BSS.
  ELF checks verify mutable state in FF0000-FF623C and absence of interpreter
  symbols; cartridge header and checksum checks pass. Emulator/hardware
  playability is **not established yet**.

See `docs/CURRENT_STATUS.md` for the exact verified state.

The project is not fully decompiled yet. No gameplay dispatch uses the instruction bridge. Five
Mega Drive presentation hooks remain empty. Dispatcher registration coverage
does not establish complete-game equivalence or a playable console build.
The audio driver passes 144,384 isolated differential updates, including RAM and
ordered PSG/stereo writes. It still needs native IRQ integration. Frame
tests share the native video/input tick; isolated video-block tests compare
the original instructions separately.

## Original game data

This repository does **not** include the original Master System ROM or generated full-ROM dumps. Provide your own legally obtained ROM locally and use the extraction/generation tools in `tools/` for ROM-derived build inputs.

Reference ROM SHA-256 used during reverse engineering:

`852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9`

## Reproduce local validation

From the repository root, with a C11 compiler and Python 3:

```sh
make prepare-rom ROM="/absolute/path/to/Golden Axe Warrior.sms"
make test test-final test-reset test-ui test-effects test-assets test-video test-pause test-scene test-full-effects test-transitions test-entry test-map-resources test-game-over test-presentation test-inventory test-menu test-services test-ending test-intro test-audio test-native-boot audit
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

It currently fails, intentionally. The probe does not prove all handler states
equivalent; differential and full-game integration validation are still needed.

## GitHub validation and Mega Drive build

Push/PR checks validate extraction failures, portability, backend structure and
C syntax without distributing the original ROM. To enable behavioral tests on
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
