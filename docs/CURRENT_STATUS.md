# Current status — V45

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
passing in GitHub Actions run 37596443981, including the actual standalone
68000 link, header/checksum checks and all 172032 rendered pixels. The fixture
is 6516 bytes (checksum 8D82, BSS 25171). No V38 full-game build or cadence
result is claimed while local execution is unavailable.

## Current scroll correction: V39

VSRAM now holds only the low five bits of SMS vertical scroll. The coarse
32-pixel component selects a rotated 28-row source name table, so all visible
source pixels obey the SMS modulo-224 wrap. Plane A and its palette-zero filler
use the same mapping. Changing the coarse base or right-column lock refreshes
all rows; subsequent dirty logical rows rotate to their physical destinations.
Right-locked name columns retain unscrolled rows.

Host tests add 49152 visible-line comparisons and 15360 independent dirty-row
mask comparisons. The production-backend fixture exercises all 256 scroll
values with/without the right-column lock, one changing logical descriptor and
sprite overlap: all 515 stages / 29532160 pixels pass in GitHub Actions run
37597060478. The standalone image is 7052 bytes, BSS 25175, checksum 187C.
Horizontal scroll is zero in the right-lock fixture; combined fine horizontal
scroll and vertical column-lock behavior is not signed off.

## Sprite boundary correction: V40

The frame-level portable sprite-status calculation now wraps SAT Y values
above D0 (the list terminator), fixing E0 in the zoomed 16-high mode. Two opaque
E0 sprites expose their final row on display line zero and must collide. Three
explicit DF/E0/E1 regressions increase the synthetic host suite to 6951 cases.

An independent generated Z80 program configures the SMS II VDP, polls its real
status port and accumulates flags until VBlank. The pinned hardware core runs
all 256 Y positions in all four height/zoom modes: 1024 two-sprite collision
cases in one generated program with no game data and no portable status implementation linked. The
new run passes in GitHub Actions 37599618930. A compiled portable-C
comparator also matches all 1024 observed status bytes directly. The probe
finishes in 3083 emulated frames. This verifies collision visibility, not
scanline-accurate
overflow timing or physical console behavior.

## Native sprite rendering: V41

The MD adapter now counts SMS SAT entries per visible line, including transparent
and off-screen-X sprites. Per-instance row masks remove pixels after the eighth
entry without removing its legal rows elsewhere. Cached copies live in MD VRAM
4000–7FFF, separate from the 512 source patterns and name tables. Each slot
reserves eight tiles, enough for a zoomed 16-high sprite (16×32 output pixels).

The adapter implements 2x horizontal/vertical zoom and uses column-first MD
pattern layout. Geometry changes update masks; source dirty bits refresh copies
even when SAT metadata has not changed. Cached tile/mask/mode values avoid
reconversion of unchanged copies. Scratch is persistent and small.

ROM-free tests add 18688 independent mask/count cases and 98304 pixel cases,
including ASan/UBSan. Seventeen extra native stages cover full/partial ninth-sprite
clipping, transparent/off-screen count consumption, zoom, tall/odd patterns,
the high pattern bank, source edits without SAT changes, list clearing and
reuse, sprite shift-left, backend reinitialization and subsequent pattern-only
edits. All 532 stages / 30507008 pixels pass in Actions 37603203186. The actual
standalone image is 9928 bytes, BSS 25943, checksum 92EA…1641 tokens truncated…to slot 1.
3. Import SRAM, continue slot 1, save to slot 2.
4. Import SRAM and continue slot 2 without saving.
5. Import SRAM, continue slot 2, overwrite slot 0.
6. Import SRAM and continue the overwritten slot 0.
7. Corrupt one signature byte, restart and check new-game entry and erased
   slots, while preserving reserved bytes and the other mapper page.

All seven pass and resume at least 300 physical gameplay frames with audio
and IRQ checks. Every observed continue checks all 592 serialized bytes
before scene entry, adjusting only C0C0/C0C1 from C0C2/C0C3 as the original
continue routine does, and checks separately restored HP and selected slot.
Save checks name, HP, return cell and currency. Between processes, only SRAM
is transferred: no emulator savestate or work RAM snapshot is loaded.

SRAM $1000-$149F is production scene/map scratch, so preservation comparisons
exclude that workspace. Slot writes are confined to their 592-byte payload
at $0400, $0800 or $0C00 and last-slot byte $0030. Host tests use distinct
payloads for overwrites; MD tests validate the production boot payload.

## Reproduction

Use the private prepared ROM and the existing native MD build. For example:

```sh
make test-save-cycle test-reset test-intro test-services
python3 tools/test_md_save_emulator.py \
  --core /path/to/genesis_plus_gx_libretro.so \
  --nm /path/to/m68k-elf-nm
```

Generated SRAM, screenshots and logs stay in ignored `md/build/save-cycles/`.
The public repository contains only code, checks and this report.

## Limits and next work

Service arrival is a controlled RAM transition from gameplay into the
production save service. All menu confirmation and SRAM writing then execute
through production C and controller input. Traveling to the sanctuary and
entering it through normal collision/interaction remains a separate route
test. Both mapper pages are covered on the native host; this MD scenario uses
the normal boot page. Physical cartridge battery behavior, power loss during
writes, PAL/NTSC hardware and a full playthrough remain unverified.
