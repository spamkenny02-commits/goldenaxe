# Current status — V26

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
- Frame tests share the native video/input tick. Full original IRQ status,
  line/asynchronous handling and audio-engine equivalence remain outstanding.
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
- Header, checksum, ELF address-map and MD source checks pass. Emulator
  and hardware playability and full-game equivalence remain unverified.

Validation locally: strict C11 Phase 17/final/reset/UI/effect/asset/Pause/scene/transition/entry/map-resource/game-over/presentation/inventory/menu/service/ending/intro suites and native-only boot, ASan/UBSan,
extraction failure tests, compiled registration coverage, portability and MD
structure/syntax checks. LeakSanitizer is disabled here because sandbox /proc
access prevents its operation; address/undefined-behavior checks remain enabled.

Reproduction: README.md. GitHub behavioral tests and manual MD builds require
private GAW_ROM_BASE64 input. Without it, CI explicitly skips behavioral tests.

Next: full IRQ and audio, complete platform hooks, full-game integration
and hardware testing.
