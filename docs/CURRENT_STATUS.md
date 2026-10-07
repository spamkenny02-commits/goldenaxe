# Current status — V44

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
standalone image is 9928 bytes, BSS 25943, checksum 92EA. Host/sanitizer checks
and all 1024 directly observed SMS status comparisons also pass.

## Full-game validation restored: V42

Local execution and the previous private reference input/toolchain were recovered.
A fresh V41 build and all host reference/differential targets pass. V42 caches
unchanged physical scroll tables; the H-scroll line handler and backend init
invalidate the cache. Four new native stages check nonzero H-scroll, restoration
after the line handler, top-16-line H-lock and backend reinitialization. All
536 stages / 30736384 pixels pass locally against the independent pixel oracle.
The combined fine H-scroll/right V-lock case remains unverified.

The V42 full game is 478284 bytes, BSS 32296 at FF0000–FF7E28, checksum 61A4.
The actual vectors/link/header/native-only checks pass. Idle advances 227 updates
in 300 physical gameplay frames, identical to freshly rebuilt V41 (V37: 239).
The controller route reaches cell 94, position [56,104], HP 24, state 0C on
both SMS and MD. It takes 571 MD gameplay frames versus 348 SMS; both sampled
update counts are 346. No cadence gain or exact input-phase equivalence is claimed.

## Sprite work reduction: V43

Collision scratch uses eight aligned 32-bit zero stores per touched line and
character-byte access with constant shifts for opacity merges. The MD line-mask
helper clamps visible rows once and advances a mask bit per line. Persistent
RAM remains unchanged at 32296 bytes; the full native image is 478324 bytes,
checksum 20D7, with RAM ending FF7E28. Actual link/vector/header checks pass.

The controller route takes 529 gameplay frames versus V42's 571 (7.4% fewer),
finishing at the same cell 94 / [56,104] / HP 24 / state 0C. Profiled master
cycles decrease from 613517949 to 572321489. Idle remains 227 updates/300 frames.
All 6951 status cases, 1024 hardware collision cases, MD helper oracles,
ASan/UBSan helper checks, IRQ/final differential checks and 536 native raster
stages / 30736384 pixels pass. The settled full-game screenshot differs from
V42 at 363 pixels at that checkpoint; V44 resolves this observation below.

## Atomic video commands: V44

The original RST $28 protects its two control-port bytes with DI/EI. Independent
C calls left an asynchronous VBlank free to cancel a partial shadow command.
All native address/register helpers now use gaw_platform_video_command: MD
saves/restores SR around the pair, while the synchronous host emits both bytes.
Scalar ports remain intact for reference/protocol testing.

The V43 mismatch is resolved: the shared 256x192 route viewport matches V42
exactly and all 49152 SMS pixels after fixed DAC conversion. All 537 fixture
stages / 30793728 pixels pass, including a forced-pending-VBlank command test.
Removing only the mask in a temporary negative build fails at stage 536 [0,0].
The stress delay is enabled in the fixture only, not the production image.

Full-game size is 479592 bytes, BSS 32296, checksum 5223, RAM end FF7E28;
actual native-only link/vector/header checks pass. The route stays at 529
gameplay frames with identical final cell/position/HP; idle measures 225/300
updates. The small idle cost is documented. This is one route's settled raster,
not a claim of full-game or physical input-phase equivalence.

## Remaining work

Continue full-game sprite/rendering performance, combined fine H-scroll/right
V-lock, exact overflow timing, controller/combat/interaction routes, SRAM
save/reload, playthrough/ending and PAL/NTSC/physical hardware behavior.
The project is not declared finished or universally recompiled.
