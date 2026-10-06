# Current status — V19

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
- One instruction-bridge call site remains: non-gameplay main-state dispatch.
- All four effect states are native for both C090/C098 slots. States 3/4 pass
  8,192 differential cursor cases; states 1/2 pass 72 complete cycles with
  per-frame RAM/VRAM comparison and final CRAM/register/SRAM/timing comparison.
- Scene restoration $16EF is native: three layers, gates, palettes, metatiles
  and SRAM animation workspace pass 36 unaccelerated original Z80 comparisons.
- Palette fade-in $0AA4, fade-out $0B12 and world reveal $1FA7 are native C.
  Their 48 comparisons cover zero/mixed palettes, display flags, input and
  Pause events; RAM, VRAM and VDP registers match after every shared frame.
  These routines are integrated into native state 08.
- Sprite animation tables below $8000 now read the fixed ROM banks instead
  of incorrectly reading bank 12. Gate restoration preserves distinct C080
  and C088 records, correcting the previous duplicate copy.
- Item graphics dispatch $2AF4 is native: 132 cases plus four compressed
  resources compared against the unaccelerated original Z80 decoder.
- Five MD presentation hooks remain empty: scroll begin/end, special effects,
  world map and transition presentation.
- Main-state registration is 6/12: Pause (02), new game (04), continue (06),
  scene entry (08), gameplay initialization (0A) and gameplay (0C). Six other
  states remain bridged.
- Complete entry sequences pass 4,148 raw original Z80 comparisons. Continue
  and scene entry cover all 512 cells, cached/changed scenery and display flags.
  RAM, VRAM and registers are compared each shared frame, with final SRAM,
  CRAM and elapsed-frame comparisons; refresh-register entropy is replayed.
- Map-entity graphics now load compressed resources and remap their pixels on
  host and MD. 6,144 comparisons cover every cell, four persistence masks and
  three boss-progression states, including RAM and all VRAM.
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

Validation locally: strict C11 Phase 17/final/reset/UI/effect/asset/Pause/scene/transition/entry/map-resource suites, ASan/UBSan,
extraction failure tests, compiled registration coverage, portability and MD
structure/syntax checks. LeakSanitizer is disabled here because sandbox /proc
access prevents its operation; address/undefined-behavior checks remain enabled.

Reproduction: README.md. GitHub behavioral tests and manual MD builds require
private GAW_ROM_BASE64 input. Without it, CI explicitly skips behavioral tests.

Next: non-gameplay states, complete asset/IRQ/video-queue
and audio services, complete platform hooks, cross-link, full-game integration
and hardware testing.
