# V41 — Render the SMS eight-sprite line limit and zoom on native MD

The previous MD adapter copied SAT entries but let MD's larger hardware sprite
limit decide which pixels appeared, and did not enlarge zoomed sprites. The
portable status calculation alone did not make the actual raster faithful.

## Change

Count SAT entries in their original order for each visible SMS line. Transparent
sprites and fully off-screen X coordinates still consume the eight-entry budget.
Each sprite gets a row mask, retaining its unblocked rows and clearing later
entries' blocked rows.

Use 64 private MD pattern slots at VRAM 4000–7FFF, eight tiles per slot. This
region does not overlap the 512 original patterns, Plane A/B, Window, H-scroll
or MD SAT. The maximum enlarged 16-high sprite becomes a 16×32 MD sprite in
column-first tile order. Smaller formats use the needed prefix of their slot.

A compact persistent cache stores source tile, mask and mode. Only changed
masks/modes/visible source patterns regenerate copies. Dirty source-pattern bits
are captured while consuming the existing dirty iterator; pattern-only changes
refresh cached copies even when the SAT has not changed. No full duplicate
pattern bitmap or large interrupt-stack array is introduced.

## Checks introduced

ROM-free helper tests compare 18688 line-mask/count cases against a scanline-first
oracle and 98304 individual pixels against unpacked source planes. The helper
suite also runs under ASan/UBSan.

The production-backend 68000 fixture adds 15 stages:
- A wholly blocked ninth sprite and a ninth with legal trailing rows.
- Transparent first-eight entries and eight fully off-screen entries.
- Zoomed 8/16-high sprites, E0/E1 top clipping, odd-index masking and tall rows.
- High pattern bank and pattern-only colour/opacity changes without a SAT write,
  including an edit to the second tile of a tall sprite.
- An empty list followed by slot reuse, and shift-left clipping.

The total native raster check is 530 stages / 30392320 pixels. This initial
checkpoint awaits the expanded run. V40's 1024 independent Z80-observed status
cases and V39's 29532160 MD pixels already pass; private reference-ROM CI tests
remain explicitly skipped without input.

## Limits and next step

Measure the actual full-game RAM/link/cadence and rerun private controller routes
when local execution recovers. Generated fixtures prove covered raster behavior,
not full-game or physical hardware equivalence. Combined fine H-scroll/right
V-lock and exact sprite overflow timing still need attention. Continue combat,
interactions, SRAM save/reload and playthrough/ending checks.
