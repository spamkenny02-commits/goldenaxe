# V23 — Native name entry and prepared dialogue

Main state 12 ($1101) now executes menu.c: menu reset, keyboard/font assets,
fixed text, grid navigation, directional-repeat timing, insertion, deletion,
name validation and the introduction following character creation.

The shared UI now exposes fixed-text source advancement, fixed sprite
descriptors ($0A78), prepared dialogue ($0524) and menu reset ($0B53). The
inventory uses the same sprite builder. Status initialization $1DEB is native.

Original $123F/$124C decrements the trailing-space pointer twice per loop in
this reference revision. Native code retains that observable behavior.

Full-name tests exposed a previous dialogue scrolling bug at $069F: after
shifting by N scanlines the original clears N rows in each bitmap column. The
native code previously cleared one row. It now matches the original complete
message, including the frame on which each scroll step is visible.

Validation: 8,064 cursor/repetition comparisons, 2,688 edit/confirm comparisons
and four complete state cycles against unaccelerated original instructions,
plus ASan/UBSan. Full cycles compare RAM outside Z80 stack, all VRAM and display
registers each shared frame, final CRAM and frame counts. The existing suites
remain green. Registration is 9/12; 00, 0E and 16 remain bridged.

Audio/full IRQ equivalence, five MD presentation hooks and a linked/play-tested
console ROM remain outstanding. Frame comparisons share native video/input.

Next: save/shop/inn services, title/intro and ending, audio/IRQ, then complete
backend integration and console testing.
