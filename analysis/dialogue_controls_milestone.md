# Dialogue controls - v0082

ROM SHA-256 365b546d3f02682d7642b10970eda3863f47d49e80602619ebef16c95006b021
1 MiB, additive checksum 0AFE. Original ROM and extracted resources unchanged.

The renderer now interprets 5C as the 0631 toggle of DCC6 bit 0, rather
than drawing a fallback glyph for a backslash. This bit controls the 05DF
extended-glyph remapping (indices 88..BE subtract 37), not ordinary ASCII case.
Width lookahead and actual drawing use the same mode. A substituted name
forces the remapped variant, then restores the enclosing text's mode, as
06F3/075E do. Numeric substitutions retain the enclosing mode.

24 invokes the 076B intermediate pause: publish the current bitmap, wait
for acknowledgement, then resume the same text without advancing the line.
The existing native page-wait marker and input aliases are retained; source
global-clock reset and IRQ/transfer ordering are still not fully reproduced.

Automatic wrapping now retries the whole word on the next line, including
an overwide word that still cannot fit at x=0. The original repeatedly moves
such a word to following lines and reaches a page wait; the native renderer
now reaches that same stable empty bitmap rather than clipping the word.
Partial word drawing/clearing within a video frame remains unverified.

Direct original-renderer comparison uses test-only copies of both ROMs:
only the opening-text resource and native additive checksum are changed.
Argument fixtures explicitly inject a name or number into RAM. Production
ROMs are never modified by the validator. Thirteen fixtures in each region
cover plain text, toggles within/across words, double toggle, wrapping,
overwide word, forced name mode, numbers 0/65/12345, pauses and explicit newline.
All 26 match stable software bitmap bytes and actual hardware bitmap/color
indices. Pause cases also match before and after acknowledgement. Sixteen
identical fixtures failed on the v0080 baseline and pass now; the ordinary
wrap fixture was additionally shortened so each word fits on a line, while
the original overwide fixture is retained as its own passing case.

Current-ROM regressions pass: four complete scroll-pose frame lists, twelve
final acknowledgement cases, six NPC dialogues plus a natural walking route,
43 merchant cases and bounded hero/scroll/eight deterministic enemy-motion
comparisons in both regions. All 29 distinct first-page source bitmap shapes
remain present in order. The first-page wait remains 9 frames late NTSC /
10 PAL; first-room readiness remains 33/31 early. Save/free-healer evidence
is still associated with v0080 and was not rerun for this change.

Replacing only glyph lookup and the renderer with their baseline definitions
reconstructs the exact v0080 main.c. Header, build padding, extracted assets
and other production routines are unchanged. v0081 remains a preserved
intermediate build; its overwide-word discrepancy was corrected in v0082.

Full parameter streams, empty/long/repeated substitutions, every text and
control combination, exact clock/marker/timing/audio and partial transfers
remain unproven. Full actor/boss behavior, abilities, quests, ending and
natural complete progression remain unfinished. Inspect missing gameplay
states next as well as remaining renderer fidelity; text checks alone cannot
establish a complete port.
