# Current status — V29

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
- No instruction-bridge call sites remain in production gameplay code.
- All four effect states are native for both C090/C098 slots. States 3/4 pass
  8,192 differential cursor cases; states 1/2 pass 72 complete cycles with
  per-frame RAM/VRAM comparison and final CRAM/register/SRAM/timing comparison.
- Scene restoration $16EF is native: three layers, gates, palettes, metatiles
  and SRAM animation workspace pass 72 unaccelerated original Z80 comparisons.
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
- Main-state registration is 12/12: title/intro (00), Pause (02), new game (04), continue (06),
  scene entry (08), gameplay initialization (0A), gameplay (0C), ending (0E), inventory (10), name entry (12) and game over
  (14) and services (16). All twelve states are native.
- Complete entry sequences pass 4,148 raw original Z80 comparisons. Continue
  and scene entry cover all 512 cells, cached/changed scenery and display flags.
  RAM, VRAM and registers are compared each shared frame, with final SRAM,
  CRAM and elapsed-frame comparisons; refresh-register entropy is replayed.
- Game over (14, $257D) is native: grayscale fade, menu graphics, input edges,
  checkpoint selection and currency penalty pass 128 complete comparisons,
  with RAM/VRAM/register checks at each shared frame.
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
- Synchronous IRQ video $013E-$0199 and queue $0293 are native and active
  in the frame tick: scroll registers, SAT, pending resource/HUD uploads, CRAM,
  ROM/RAM/SRAM blocks and descriptor rectangles. 256 isolated comparisons
  execute original instructions up to $019C at a fixed VCounter; audio/input
  are excluded from this reference block.
- Mega Drive uploads the shadow after the native video tick in the same
  platform barrier. This ordering is checked at source level, not on hardware.
- Frame tests share the native video/input tick. Full original IRQ behavior is also compared independently below.
- Inventory (10, $70F2) is native: fonts, item icons, visited dungeon map,
  blinking location marker, equipment selection and scene restoration pass
  432 complete original-instruction comparisons. Each shared frame compares
  RAM/VRAM/registers; final CRAM/SRAM and timing are also checked.
- Name entry (12, $1101), keyboard cursor/repetition ($12C1), editing and
  confirmation ($11BA), resources and following message are native. Tests
  compare 8,064 cursor cases, 2,688 input cases and four complete cycles with
  per-frame RAM/VRAM/register checks. The long message detects and verifies
  a scroll fix: all shifted-out bitmap rows are cleared, not only the last.
- Save/shop/inn/magic-upgrade state 16 ($7390) is native, including portrait
  masks, saved-slot names, prices, purchases, healing, refusal paths, magic
  capacities and SRAM slot copies. 1,024 cursor cases, 25 drawing cases and
  72 full cycles compare RAM/VRAM/registers each shared frame, final CRAM,
  all SRAM and timing. The two-stage descriptor decoder $0BD3 is native.
- Scene restoration now places its animation workspace on the selected SRAM
  page; scene tests cover both pages in 72 cases.
- Ending (0E, $6EBE) is native, including enemy-drain loop, centering, crystal
  reveal, palette blackout, font loading and scrolling credits. Four complete
  sequences compare RAM/VRAM/CRAM/registers every shared frame, final SRAM
  and elapsed frames. Centering cases detected a missing walk-pose increment
  at $3309; blocked and successful movement attempts now advance the pose.
- Title/intro (00, $146D/$0C98), scene/text/actor/palette animations and
  new/continue selection ($14ED) are native. Twenty complete comparisons
  cover attract mode, five intro skips, new game, three saved slots on both
  SRAM pages, empty-slot refusal and button/cursor cancellation. RAM outside
  the reference stack plus obsolete C02A SP metadata, VRAM/CRAM/registers
  are compared every shared frame; final SRAM and frame totals match.
- Host integration boots through title, name creation, new-game setup and
  24 gameplay updates without linking the instruction interpreter. The MD
  production source list also excludes sms_compat.c/recompiled.c.
- Native 68000 cross-link now passes with m68k-elf GCC 14.2.0. The ROM is
  427,470 bytes, BSS 25,148 bytes, reset entry $000200 and checksum $F87C.
  A critical empty-.data linker issue had placed BSS after ROM text; explicit
  ROM/RAM memory regions now put mutable state at $FF0000-$FF623C. Actual
  ELF checks verify all B/D symbols are in work RAM and no interpreter
  symbols are linked. memmove is provided by the freestanding runtime.
- Header, checksum, ELF address-map and MD source checks pass. Emulator boot is verified below; hardware and full-game equivalence
  remain unverified.

Validation locally: strict C11 Phase 17/final/reset/UI/effect/asset/Pause/scene/transition/entry/map-resource/game-over/presentation/inventory/menu/service/ending/intro suites and native-only boot, ASan/UBSan,
extraction failure tests, compiled registration coverage, portability and MD
structure/syntax checks. LeakSanitizer is disabled here because sandbox /proc
access prevents its operation; address/undefined-behavior checks remain enabled.

Reproduction: README.md. GitHub behavioral tests and manual MD builds require
private GAW_ROM_BASE64 input. Without it, CI explicitly skips behavioral tests.

- Bank 6 audio driver $8000 is high-level C: seven sequencer channels,
  request priorities, overlays, pause, fades, note durations, pitch waves,
  vibrato, envelopes, stream loops/calls and stereo control. 144,384 isolated
  original-instruction updates compare RAM C000-DF8F and every ordered
  PSG/stereo write, with refresh entropy replay. Tests cover all 13 music
  commands, 29 effects, both DE03 timing modes and mixed command sequences.
  Unused/reserved malformed stream requests report diagnostics. The driver is now active in the native frame loop; emulator audio
  and hardware behavior are still being verified.

- Complete IRQ $0038 is native: status acknowledgment, synchronous video/audio/
  input/timers, asynchronous audio/timer updates and all three line callbacks.
  3,072 isolated raw-original comparisons check RAM, VRAM, CRAM, registers,
  status reset and ordered sound writes; 256 cases check NMI. IRQ ASan/UBSan
  passes. Shared-frame suites still use the native tick on both sides.
- Game sound requests now write their original DE06/DE08 queue slots; no game
  command is sent directly to PSG. Corrected two world barriers that had bypassed
  C02E, linked-room wipe timing and room-entry/return fades. Impacted gameplay,
  menu, inventory, service, ending, entry, effect and UI regressions pass.
- 68000 link includes audio/IRQ and passes RAM/ELF/header checks: 432,418 bytes,
  BSS 25,152 bytes at FF0000-FF6240 and checksum FB5E. MD still polls synchronous
  barriers; asynchronous and line hardware scheduling is the next backend task.

- Genesis Plus GX (49c584764893b0505ac7f768a754f97330fa4392) executes the
  native ROM through title, name creation, new-game setup and 300 emulator
  gameplay frames at cell 95, HP 24, with visible graphics and audible PSG.
  It does not establish a full-game playthrough or hardware correctness.
- Fixed disabled-display VBlank polling, full-screen Window masking and an
  opaque Plane B alias; empty SAT now clears old sprites and wrapped sprite Y
  coordinates are converted correctly. Colors use full MD DAC range. A bit
  expansion lookup accelerates pattern conversion; unchanged shadow bytes
  no longer trigger unnecessary uploads. 5,120 pattern rows, 64 colors, 8,192
  descriptors and 256 sprite positions pass independent conversion checks.
- Current linked image is 433,646 bytes, BSS 25,152, checksum 6CD6. Frame
  cadence is still limited by the C backend; audio/line hardware IRQ scheduling
  and further performance work remain, as do the five presentation hooks.

- MD level 6 VBlank and level 4 line interrupt vectors now call the portable
  IRQ through register-preserving 68000 trampolines. VBlank continues native
  sound/timers asynchronously while the main thread computes. Physical uploads
  mask line IRQs while leaving VBlank enabled; Start provides Pause NMI.
  NTSC uses DE03=80, independently observed in the original SMS emulator.
- With O2/LTO and dirty name-table rows, the private boot check records 139
  gameplay updates in 300 physical frames (299 VBlank, 160 async), plus 45
  line IRQs during boot. This improves the previous 70 updates but is still
  slower than the original SMS check's 298 updates. It is not a full playthrough.
- The linked image is 471,702 bytes, BSS 25,174 at FF0000-FF6256, checksum 6178.
  Actual ELF vectors, mutable symbols and interpreter exclusion pass. Fixed
  ROM-end metadata for odd-sized link images before checksum generation.
  Standalone video/MD conversion, 256 presentation cases, 3,072 full IRQ cases,
  256 NMI cases and native-only boot regressions pass.

- The remaining player presentation actions now run in portable C: 16-frame
  rotating transition, 40-frame interior palette sequence, gradual healing,
  teleport wipe, eight-pass terrain pattern transformation and the overworld
  overview generated from all 225 cells. The obsolete special-effect, map and
  transition-frame platform hooks are removed after implementing their work.
  48 raw-original comparisons check RAM C000-DF8F, VRAM, CRAM and registers
  at every shared frame, plus final SRAM and exact barrier totals. ASan/UBSan
  passes. The reference step budget now accommodates the map's long generation
  between barriers; frame tests still share native IRQ scheduling.
- Current MD image is 473,672 bytes, BSS 25,174, checksum A28D. Native boot,
  attack, Pause/resume, inventory open/close and four-direction movement still
  execute on the actual 68000 emulator backend. Two empty scroll hooks remain.

- Screen scrolling $2051-$229B is now complete portable C: original buffer
  swaps, row/column uploads, sprite displacement, frozen barriers, line-scroll
  setup/reset and neighboring-cell reload order. Corrected the five-stage route
  puzzle at cell 77, including the valid exit to 76 and final exit to 67.
  220 complete raw-original comparisons cover four directions, three layers,
  edge cells, sprite-order phases and no-crossing cases. 320 independent route
  comparisons and ASan/UBSan pass. Every shared frame compares RAM C000-DF8F,
  all VRAM/CRAM/registers; final state and exact barrier totals match.
- The last two platform hooks are removed after implementing the actual scroll.
  The compiled completion gate passes: 12/12 states, 127/127 entity types,
  512/512 world entries, zero instruction-bridge calls and zero empty MD hooks.
  This gate measures coverage; it does not prove all game states or a playthrough.
- Current MD image is 474,504 bytes, BSS 25,174 at FF0000-FF6256, checksum CA4B.
  ELF/vector/header checks and the native-only boot regression pass. A longer
  physical-controller sequence on MD and original SMS advances 890 gameplay
  updates at cell 95 with the same recorded player positions and HP 24. Terrain
  keeps that route inside the initial screen; emulator screen crossings remain
  to be exercised. The MD path takes more physical frames than SMS.
- The execution environment disconnected after these checks. The tested source
  changes and this status were preserved through the Git API; profiling and
  further runtime validation require restoring the local execution environment.

- V33 adds frame-level SMS Mode 4 sprite status: the eight-per-line limit,
  opaque pixel collisions, terminator, clipping/wrap, height/zoom and pattern
  bank. A cache recomputes on VRAM/configuration writes; each VBlank latches the
  flags anew and status reads clear them normally. This supplies the overflow
  flag used by the original gameplay renderer.
- Private cartridge reads moved to src/rom.c so the video shadow and its new
  status calculator link without ROM data. Both host and MD source lists include
  the new modules. CI runs 6,948 independent synthetic comparisons against a
  pixel/scanline oracle, then the same cases under ASan/UBSan; both pass.
  Strict C11 syntax, portability/backend audits and MD conversion tests pass.
- The last complete original-game differential run and actual 68000 image are
  V32. V33's reference-ROM regressions, 68000 rebuild, sprite output/clipping and
  emulator profiling have not run: the terminal remains disconnected and CI
  has no private ROM input. Reference-ROM steps are explicitly skipped in CI
  when that input is absent. No placeholder game data is executed.
- Git saves include V33. These flags are frame-level, 192-line Mode 4 status;
  they do not establish cycle-accurate timing or physical-hardware equivalence.

Next: rebuild and rerun V33 reference/68000 tests, then profile MD cadence,
validate actual sprite clipping, cross screens through controller input,
complete full-game replay/integration and test physical hardware.
