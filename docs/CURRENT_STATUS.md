# Current status — V14

Objective: faithful Golden Axe Warrior decompilation into portable C, then
platform backends, including native Motorola 68000/Mega Drive.

- Actual compiled dispatchers register 127/127 entity types and 512/512 world
  callbacks as native/RET. Registration is not an equivalence proof for every
  state of every handler.
- World scripts ADEE, B00A and B19E now use native C. The world-dispatch
  instruction fallback has been removed.
- Native UI handles dialogue glyphs, word wrapping, substitutions, numbers,
  page pauses, scrolling, three Yes/No menus, borders and name-table uploads.
- UI/script differential tests compare RAM outside Z80 stack workspace,
  complete VRAM, CRAM, VDP registers and elapsed frames. Tests include 46
  deterministic interactive branches and 285 card draws with replayed entropy.
- Reset/save initialization $0404 and initial SMS VDP setup $03C0 are native C;
  reset tests cover 58 SRAM cases and complete VDP state.
- Three instruction-bridge call sites remain: effect-state slots C090/C098
  and non-gameplay main-state dispatch.
- Eight MD presentation hooks remain empty: resource uploads, scroll begin/end,
  inventory, special effects, world map and transition presentation.
- ROM/VDP shadow services still live in sms_compat.c alongside the interpreter.
  These must be separated before removing that file from console builds.
- No linked/play-tested Mega Drive ROM has been produced.

Validation locally: strict C11 Phase 17/final/reset/UI suites, ASan/UBSan,
extraction failure tests, compiled registration coverage, portability and MD
structure/syntax checks. LeakSanitizer is disabled here because sandbox /proc
access prevents its operation; address/undefined-behavior checks remain enabled.

Reproduction: README.md. GitHub behavioral tests and manual MD builds require
private GAW_ROM_BASE64 input. Without it, CI explicitly skips behavioral tests.

Next: effect dispatch and non-gameplay states, separate asset/VDP services,
complete platform hooks, cross-link, full-game integration and hardware testing.
