# V17 — complete native world effects and scene restoration

Lifted the two remaining full-screen world effects ($6AFB and $6C2E): fire/wave
animation, eight orbiting sprites, palette pulses, enemy damage and complete
scene restoration. All four effect states now execute C at both state slots;
the animation dispatcher no longer calls the instruction interpreter.

Added native scene restoration $16EF: four-plane tile decoding, interleaved
RAM RLE, gate records, interior palette selection, auxiliary metatile records
and SRAM animation workspace. Corrected gate restoration to copy distinct
C080/C088 records and renderer lookup to use fixed banks below address $8000.
The latter was revealed by the first per-frame effect comparison.

Validation:

- 72 complete effect cycles: two effects, two slots, three environment layers,
  three starting frame phases and two player positions including a screen edge.
- RAM C000-DF7F and all VRAM compared after every shared frame tick; final
  CRAM, VDP registers, all 32 KiB SRAM and elapsed frame counts also compared.
- Enemy cases cover absent entities, zero width, flags, armor exceeding damage
  and hit-accumulator wrap. Final equipment/scene/HUD restoration is included.
- 36 scene cases compared against original Z80 execution with the resource
  decoder accelerator disabled, covering gate conditions and interior palettes.
- Existing strict C11 and ASan/UBSan suites, cursor cases, Pause, UI, tools,
  portability and MD syntax/structure checks remain required.

The frame trace uses the shared IRQ replacement. It does not establish original
SMS IRQ, video queue or audio-engine equivalence. Scene SRAM is deliberately
included because $16EF writes animation data through the mapped RAM window.

Remaining: one interpreter call site serving nine main states, six MD hooks,
IRQ/video queue/audio integration, full-game tests and a linked/play-tested MD
build. Registration remains 127/127 entities, 512/512 world, 3/12 main states.
Reference ROM data stays local and ignored.
