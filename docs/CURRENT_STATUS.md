# Current status — V38

Objective: faithfully decompile Golden Axe Warrior into portable C and run it
through native platform backends, including Motorola 68000/Mega Drive.

## Native game core

The compiled coverage gate registers 12/12 main states, 127/127 active entity
types and 512/512 world callbacks as native/no-op. The production MD image links
no Z80 interpreter or instruction bridge and has no empty presentation hooks.
Registration alone is not proof of full-game equivalence.

Reset/save, title/intro, name entry, new/continue, scene entry/restoration,
gameplay, screen scrolling, dialogue/menus/services, Pause, inventory, player
special items, world effects/transitions, game over and ending are portable C.
ROM data access, decompression, VDP presentation, synchronous/asynchronous IRQ
and PSG/audio use native services.

V37 reran all local original-instruction differential/regression suites and
ASan/UBSan successfully, plus the compiled coverage gate. Local LeakSanitizer
process inspection is unavailable; address/undefined-behavior checks ran with
leak detection disabled. Full case counts and previous milestones are recorded
in README.md and the CONTINUOUS_Vxx_PROGRESS reports.

ROM-free CI independently checks VDP port/block equivalence (4274 cases),
sprite status (6948 cases) and pattern/palette/descriptor conversions. V37's
GitHub Actions host validation completed successfully; private-ROM comparisons
are conditional on the private input and must not be inferred from skipped CI
steps.

## Last measured full-game Mega Drive image: V37

- 476460 bytes; BSS 31518 at FF0000–FF7B1E; checksum BC9D.
- Actual linked vectors, writable state, interpreter exclusion, ROM header and
  checksum checks pass. Emulator boot, name/new-game entry and audio pass.
- Idle advances 239 gameplay updates over 300 physical frames (V36: 148;
  V35: 136). SMS advances 298/300 in the same idle observation.
- A normal-controller route crosses cell 95 to 94 and settles at [56,104],
  HP 24 and state 0C on SMS and MD. MD takes 508 gameplay physical frames;
  SMS takes 348. Sampled C-state update counts are 345/346 respectively.
  Exact physical/input phase is not claimed.
- V36 also checks attack, Pause/resume, inventory open/close and movement.

## Current rendering correction: V38

Real SMS/MD screenshots exposed black grass where SMS displays background
palette entry zero. MD tile pixel zero is transparent. V38 supplies both SMS
palette-zero colours on a low-priority Plane B beneath the converted Plane A.
Both planes share scrolling and dirty name-row updates. The bottom Window mask
uses its own tile pixel/CRAM entry; the black-palette line handler updates the
extra physical colours.

All 8192 descriptor zero-layer mappings and 1024 indexed priority combinations
are added to the ROM-free host test. A standalone generated 68000 video fixture
links the actual production video adapter and shadow, without original game
data or game dispatcher. Its emulator oracle checks 172032 pixels over palette,
sprite-overlap, dirty-descriptor and viewport stages. The new checks are
pending at this checkpoint; no V38 full-game build or cadence result is claimed
while local execution is unavailable.

## Remaining work

Correct SMS's 224-pixel vertical wrap on MD's 256-pixel name plane. Extend the
hardware fixture to all scroll values and confirm actual private-game pixels
and cadence when execution recovers. Then validate rendered eight-sprite line
clipping, more controller/combat/interaction routes, SRAM save/reload,
playthrough/ending and PAL/NTSC/physical hardware behavior. The project is not
declared finished or universally recompiled.
