# Opening setup - v0076

ROM SHA-256 a171c53496510b0e93fde0518fe517243a8fe55f78e310edf968eee53abd1b3d
512 KiB, additive checksum 3815. Native 68000 code with SGDK.

The original 1197..11B4 prelude is now represented before the opening story:
music fade controls, fade of the name screen, sprite/map clearing, menu and
equipment palette restoration, original font decompression/upload and fade-in.
0B48 falls through to 0B53, so it clears the display after fading, rather
than simply returning after the music controls. The generic world/healer
fade helper is unchanged; the new opening helper publishes prepared colors
after the next interrupt, reproducing the source palette transfer delay.

The original bank-4 A74C font stream is loaded before fading in, rather than
again in the non-overlay text renderer. Overlay dialogues retain their font
restore. Source font decompression/upload costs 70986 foreground Z80 T states
with IRQs masked. Its one/two video-frame interval is compensated in the
native world clock; this does not solve the global clock elsewhere.

Unmodified ROMs, natural scripted new game with name A, no RAM injections:

| Measurement | SMS NTSC | MD NTSC | SMS PAL | MD PAL |
| --- | --- | --- | --- | --- |
| Story routine entry | 1490 | 1490 | 1489 | 1489 |
| First page wait | 1596 | 1582 | 1583 | 1574 |
| Initial room active | 2454 | 2421 | 2448 | 2417 |

The old v0071 story entry was 40 frames early in NTSC / 39 in PAL. This
setup gap is resolved for the measured sequence. First-page waits remain
14 / 9 frames early; initial-room readiness remains 33 / 31 frames early.
Those are explicit remaining discrepancies, not passing synchronization tests.

Actual serialized CRAM entries 0..30 match on all 41 sampled video frames
1449..1489: 2542 words across PAL and NTSC. The serialized MD representation
packs internal three-bit channels, not the usual VDP register word encoding.
Color 31 retains global-clock phase differences, listed in the report.
The original 512 font bytes match SMS VRAM and native software VRAM; the
16 corresponding native hardware tiles match all 1024 source pixel colors.

Current-ROM regressions pass: complete four-pose first-page scroll frame
lists, twelve final dialogue acknowledgements, six NPC dialogues plus a
natural walking/conversation route, and bounded hero/scroll/eight deterministic
enemy-motion comparisons in PAL/NTSC. Merchant, save and free-night checks
remain evidence from v0070 and were not rerun for this opening-only change.

Removing the new prelude/helper and restoring the original font call site
reconstructs the exact v0071 main.c. Prior extracted assets, healer code,
packed dialogue LUT and dungeon animation resource hashes are unchanged.
Intermediate v0072..v0075 binaries are preserved as superseded experiments.

Next: trace 7444/779B/0524 through the first 07F4 wait to explain the residual
14/9 frames from actual preparation, rendering and IRQ suppression. Profile
initial-room resource loading separately. Global page-clock reset, complete
dialogue pixels, full enemy/boss behavior, abilities, quests, natural complete
playthrough, ending and audio waveform fidelity remain unfinished.
