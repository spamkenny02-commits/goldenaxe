# V32 — Complete screen scrolling and the native coverage gate

Implemented $2051-$229B in portable C: scratch/name-table buffer swaps, twenty
vertical row passes, thirty-two horizontal column passes, sprite displacement,
frozen VBlank barriers, line-scroll enable/reset and neighboring-cell reload
order. The screen is no longer replaced immediately before its strip animation.
The final upward buffer swap is preserved. Interior palette selection shares
the already-tested bank-5 routine.

Corrected the route puzzle at cell 77. The ordinary exit to 76 is valid; other
attempts keep cell 77 while advancing or resetting the five-stage route, and the
last successful exit moves to 67. Entity presence persistence and nibble wrap
match the original.

220 complete original-instruction comparisons check all four directions across
eleven cells and all three layers, sprite-order phases, valid interior markers,
edge cells and no-crossing cases. Every shared frame compares RAM C000-DF8F,
VRAM, CRAM and registers; final state and exact barrier totals match. A further
320 isolated route comparisons and ASan/UBSan pass. Item, final, entry and native
boot regressions pass. Frame tests still share the native IRQ; the independent
full-IRQ suite remains the separate reference for IRQ behavior.

Removed the final two platform hooks after implementing their work. The rebuilt
registration probe and --require-complete gate pass: 12/12 main states, 127/127
entity types, 512/512 world entries, no instruction bridge calls and no empty MD
presentation hooks. Coverage is not a proof of every state or a full playthrough.

The 68000 image is 474,504 bytes, BSS 25,174 at FF0000-FF6256, checksum CA4B, with
actual ELF/vector/header checks passing. A longer physical-controller sequence
on MD and original SMS advances 890 gameplay updates, with matching recorded
positions, cell 95 and HP 24. It stays in the initial screen because of terrain;
an actual emulator screen crossing is still to be exercised. MD physical-frame
cadence remains below SMS. Sprite overflow/collision status synthesis and broader
game/hardware validation also remain.

The execution environment disconnected after the successful checks. The tested
changes were reconstructed from their exact patches against V31 and preserved
through the Git API. Further profiling/runtime checks require restoring local
execution; private ROMs, emulator binaries, screenshots and state are excluded.
