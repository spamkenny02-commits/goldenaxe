# V19 — complete native new-game, continue and scene-entry states

Registered main states 04 ($2433), 06 ($246F) and 08 ($24B6) as native C.
They now compose original defaults/checkpoint positioning, equipment graphics,
scene-bank selection, fade-out, map loading, HUD, entity/player initialization
and the world reveal. The dispatcher reaches gameplay state 0C without the
instruction bridge for all three entry paths.

Replaced the empty map-entity graphics hook on host and Mega Drive. The native
resource loader reads bank/source/color-remapping records at bank 2:$825F,
decodes the original four-plane streams and applies pixel remapping where
requested. Compacted graphics slots are obtained from the decoder's actual
end position instead of a separate precomputed resource-span table.

Validation:

- 4,148 complete unaccelerated original Z80 entry comparisons: 04 defaults
  over representative prior cells, plus 06 and 08 over all 512 cells with
  four cache/display combinations, input edges and a Pause event.
- Per-frame RAM C000-DF7F, all VRAM and VDP register comparison. Final CRAM,
  all 32 KiB SRAM, frame count and gameplay state are compared as well.
- Z80 refresh-register observations are replayed as platform entropy so
  random-cell seeding can be compared deterministically.
- 6,144 map-resource comparisons: every cell, four persistence masks and
  three boss-progression states, with all RAM outside the Z80 stack and VRAM.
- Strict C11 regression suites, new entry/resource ASan/UBSan suites, MD
  syntax and portability/structure checks. No original ROM dump is committed.

Coverage is now 6/12 main states, 127/127 entity types and 512/512 world
callbacks. Six main states, one bridge call site and five empty MD hooks
remain. The IRQ replacement is shared with the reference tests; original
IRQ/video-queue/audio equivalence and a linked/play-tested MD ROM are still
outstanding. These counts do not establish full-game completion.
