# Golden Axe Warrior — SMS decompilation / native Mega Drive port

Faithful decompilation of **Golden Axe Warrior** (Master System) into portable C, with a native Motorola 68000 / Mega Drive backend.

## Current status (V16)

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
  now measured explicitly: 3/12 native states.
- Strict C11 tests, differential/regression tests, ASan/UBSan and the 68000 portability audit pass on the current working tree.
- A linked/tested Mega Drive ROM is **not claimed yet**.

See `docs/CURRENT_STATUS.md` for the exact verified state.

The project is not fully decompiled yet. Full-screen effect states 1/2 and non-gameplay states still use the instruction
bridge at two call sites. Six
Mega Drive presentation hooks remain empty. Dispatcher registration coverage
does not establish complete-game equivalence or a playable console build.
Original IRQ/video-queue handling and the audio engine also need full native
integration; current frame tests use the shared IRQ replacement.

## Original game data

This repository does **not** include the original Master System ROM or generated full-ROM dumps. Provide your own legally obtained ROM locally and use the extraction/generation tools in `tools/` for ROM-derived build inputs.

Reference ROM SHA-256 used during reverse engineering:

`852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9`

## Reproduce local validation

From the repository root, with a C11 compiler and Python 3:

```sh
make prepare-rom ROM="/absolute/path/to/Golden Axe Warrior.sms"
make test test-final test-reset test-ui test-effects test-assets test-video test-pause audit
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
successful link/header check will still require emulator and hardware testing;
it does not establish playability. Build artifacts contain game data.

For a sandbox where LeakSanitizer cannot inspect `/proc`, run
`ASAN_OPTIONS=detect_leaks=0 make test-sanitize`; address and undefined-behavior
checks remain enabled. Leak checking is enabled by default elsewhere.

## Goal

The goal is not an approximate rewrite. Gameplay behavior is lifted from the original Z80 program and checked against original execution wherever practical; platform-specific SMS presentation/hardware behavior is isolated behind the platform layer and replaced by a Mega Drive implementation.
