# Current status — V16

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
- Two instruction-bridge call sites remain: full-screen effect states 1/2
  (shared dispatch for C090/C098) and non-gameplay main-state dispatch.
- Effect states 3/4 are native: 8,192 differential cases across both slots,
  cursor coordinates and counter edge cases. Bridged effects now receive
  the original IX pointer instead of zero.
- Item graphics dispatch $2AF4 is native: 132 cases plus four compressed
  resources compared against the unaccelerated original Z80 decoder.
- Six MD presentation hooks remain empty: map-entity resource uploads, scroll
  begin/end, special effects, world map and transition presentation.
- Main-state registration is 3/12: Pause (02), gameplay initialization (0A),
  gameplay (0C). Nine other states remain bridged.
- Pause $00F4 is native, including font/text, NMI resume, equipment restoration
  and two sound delays; 48 complete differential cycles pass.
- Inventory graphics $7219/$722A and pixel remapping $1D0D are native. Sixteen
  remapping cases compare full video and scratch RAM against original execution.
- Corrected VDP I/O aliases in the reference interpreter. Original $1D0D writes
  commands through port BD, a hardware alias of BF. All 32 port pairs are tested.
- ROM/VDP shadow services now live in video.c independently of the interpreter.
  The standalone video test links no instruction interpreter. Native item
  graphics loading uses assets.c on both host and Mega Drive.
- Frame synchronization uses a shared replacement for the original IRQ. The
  differential suites do not establish original IRQ/video-queue/audio-engine
  equivalence. Those services also require lifting and integration validation.
- No linked/play-tested Mega Drive ROM has been produced.

Validation locally: strict C11 Phase 17/final/reset/UI/effect/asset/Pause suites, ASan/UBSan,
extraction failure tests, compiled registration coverage, portability and MD
structure/syntax checks. LeakSanitizer is disabled here because sandbox /proc
access prevents its operation; address/undefined-behavior checks remain enabled.

Reproduction: README.md. GitHub behavioral tests and manual MD builds require
private GAW_ROM_BASE64 input. Without it, CI explicitly skips behavioral tests.

Next: full-screen effects and non-gameplay states, complete asset/IRQ/video-queue
and audio services, complete platform hooks, cross-link, full-game integration
and hardware testing.
