# Three-scene reveal and actor diagnostics on v0030

The ROM is unchanged: SHA-256
`c325609b47f43b324624a254be204fd89f59856ace4b2460f4e588f06f05cea1`.
These read-only measurements extend the first-scene checks without generating
a new cartridge version.

`profile_intro_scenes.py` runs natural boot for 3750 frames in both regions and
reads hardware VRAM around all three scene loads. All 24 reveal passes on each
console/region start five frames apart and finish on their fifth sampled frame.
All 9216 normalized planar bytes match at each of the 48 completed native passes.
The code asserts those properties, not merely their first/last row values.

Scene starts still differ. Native first-mask offsets are -12/-14 frames for
scene 1, -18/-20 for scene 2 and -19/-20 for scene 3 (NTSC/PAL). Completed-pass
cadence does not establish equal loading duration or equal partial scanlines.

`profile_intro_actors.py` runs 6000 natural-boot frames per system/region with
no buttons or RAM writes. It compares actor state and pose vectors at matching
scene, eight-bit animation counter and clock modulo four. SGDK vtimer is read
as a 32-bit big-endian value, using its low word. All 3744 NTSC and 3772 PAL
native samples have a matching logical state in the source observations.
This phase-key comparison does not establish absolute animation timing: the
counter can wrap, and matching states are collected across observed epochs.

The profiler also reads hardware sprite tables. Native positions are normalized
by removing the canvas origin and SAT coordinate bias; native tile indices are
mapped back to SMS sprite indices. These tables are compared at matching logical
states and phases. There are **118 NTSC and 111 PAL mismatches**, so hardware
sprite equivalence is explicitly unverified. Of these, 58/49 are scene 2 and
60/62 scene 3. Most occur at clock phase 1. For example, at native NTSC frame
1898, actor 0 has pose 1 and displays tile A1; source observations with the same
counter/clock/logical state still display A0.

The next investigation should examine the relation between source 1061/108B
actor updates, 0978 sprite upload and frame sampling, versus native intro_tick
and VDP_updateSprites. A fixed delay has not been introduced: the observed
mismatches are not yet explained sufficiently to justify one. Sprite pixel
patterns, palettes and scanline timing are not covered by this SAT comparison.

`intro_scene_profiles_audit.json` binds the two profiles and profiler source
hashes to the existing cartridge. It explicitly records that the 229 SAT
mismatches remain. The v0030 archive retains both diagnostics alongside its
earlier passing targeted reports. The full port is still incomplete.
