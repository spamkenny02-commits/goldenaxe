# Title animation cadence - v0016

Native 68000 correction of the title sequence (source Z80 1470..14E9,
165C..16CD and 0AA4/0B12/0ADE). ROM: `versions/v0016-9a022782/gaw-megadrive-v0016.bin`.

The previous implementation uploaded the entire 768-cell tilemap after every
cape pose and every logo row. During active display this consumed additional
video frames. It also waited six IRQs between logo rows, whereas source 163F
waits one, and initialized the warrior's brightest color immediately.

The title now queues only modified cells using SGDK DMA. The original 33 cape
poses last six video frames each; all eight logo rows appear at one frame per
row. The original two palette ramps are restored: nine blue/green/red steps
at two frames each, followed later by nine red/green/blue steps at six frames
each. Color 1 remains zero until the warrior's final ramp, as required by the
LDIR at 14B7..14C1 (the source clears indices 1..10, not 2..11). The preceding
story fades to black in the component order and two-IRQ cadence of 0B12.

Verification uses live execution of the original SMS ROM and native MD ROM in
the official Genesis Plus GX core, without RAM writes. Four cases cover PAL
and NTSC, both with the normal intro-skip button and after the complete intro.
The source and native hardware tilemaps follow all 42 expected states (33 cape
poses, restored map, eight logo rows), with the same intervals. All 18 palette
states match byte for byte and have the same intervals. Twenty representative
video images per case (80 total) match every pixel after palette normalization.
Native palette updates precede the corresponding map DMA by one frame at some
boundaries; this comparison does not claim cycle-level synchronization.

The title still starts earlier in a natural boot: native map states are 11
frames early in NTSC and 26 in PAL; palette states are 12 and 27 frames early.
The source's compressed asset loading takes longer, and the preceding story
already has an absolute start offset. The animation cadence itself has no
accumulating drift. Absolute boot timing remains unfinished.

The 65 story text/scene maps, hero and exterior-scroll timing in both regions,
and merchant interactions/reveal are rechecked against this binary. These are
targeted checks; the complete game and all enemy behaviors remain unfinished.
See `validation/title_patch_audit.json` for exact hashes of the ten reports.
ROM versions v0014 and v0015 are preserved intermediate builds; v0016 is the
validated result of this change. v0013 remains available for comparison.
