# V22 — Native inventory

Reconstructed main state 10 ($70F2) in inventory.c. The original two-panel
inventory includes nineteen icons, its equipment cursor, the blinking current
cell marker, and the dungeon map clipped by both visited-cell flags and the
dungeon row masks. Closing it restores scene resources, player sprite metadata,
SAT, world descriptors, HUD and equipped graphics.

Shared native UI services now cover $0818, $085B, $0C36 and $20DA. The masked
glyph loader ($0365) is available to other remaining menus. The runtime
registration advances to 8/12; states 00, 0E, 12 and 16 remain bridged.

Validation: 432 complete cycles against unaccelerated original $70F2. Cases
cover three layers, twelve starting selections, three directional scenarios,
four ownership/resource variants, confirm/cancel edges and an NMI Pause event.
RAM outside Z80 stack workspace, all VRAM and registers are compared at every
shared video/input frame; final CRAM, SRAM and frame counts also match. The
inventory suite passes address/undefined-behavior sanitizers.

These comparisons share the native video/input tick. They do not establish
full original audio/IRQ equivalence or Mega Drive hardware playability.

Next: name entry, remaining title/shop/end states, audio and IRQ integration,
then complete backend and console validation.
