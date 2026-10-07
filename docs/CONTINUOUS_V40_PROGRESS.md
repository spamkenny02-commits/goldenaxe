# V40 — Zoomed sprite top-edge collision boundary

The old portable status helper and its scanline oracle both treated Y <= E0
as below the screen. That shared assumption missed E0's final visible row in
16-high, 2x zoom mode. SAT D0 terminates traversal; larger Y coordinates wrap
above the 192-line viewport.

## Change

Wrap values above D0. E0's top is -31 and its 32 output rows end on display line
zero; DF ends before line zero, while E1 exposes two rows. Keep the persistent
collision/count workspace and frame-level status cache semantics unchanged.

The host test's independent scanline oracle uses the corrected boundary.
Three explicit DF/E0/E1 cases exercise odd-index masking and opaque pixels from
the second pattern, raising the existing suite from 6948 to 6951 comparisons.

## Independent hardware check

A generated 32 KiB fixture contains only a small Z80 program and its own
patterns. It configures an SMS II VDP, clears VRAM, places two opaque overlapping
sprites, polls BF and accumulates collision/overflow bits until VBlank. It
publishes those observed flags in RAM. Neither original-game data nor the
portable C status helper is loaded into this reference.

The generated program probes all 256 Y values in the four 8/16-high,
normal/zoom modes, recording 1024 status values in RAM. The pinned Genesis
Plus GX core completes this in 3083 emulated frames. A compiled portable-C
comparator matches every observed byte directly. GitHub Actions 37599618930
passes both host and native-video jobs, including the 6951-case host suite and
all 29532160 MD pixels. The program runs without reloading the core between
cases, avoiding its unsafe reinitialization after unload with a forced model.
It verifies collision visibility, with two sprites so no overflow is expected.
Frame-level overflow timing and physical-hardware quirks are not signed off.

The completed V39 standalone native raster checks remain 515 stages /
29532160 pixels (Actions 37597060478). Full private-game rebuild/cadence and
controller/playthrough verification remain unavailable locally; no full-game
result is inferred from these generated fixtures.

## Next

Implement and verify actual native eight-sprite-per-line rendering, including
clipped rows and zoom, then resume private-game performance, controller/combat,
SRAM save/reload and playthrough checks when execution is restored.
