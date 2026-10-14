# Post-scroll bitmap publication - v0071

ROM SHA-256 b361381750ac3366da528a8d544864b2b097a6b5fffaf363d935ef5bb068e1f8
512 KiB, additive checksum CA60.

Original 06D6 calls 0786 again after the four scroll increments and before
parsing/drawing the next word. The native scroll helper now performs that
additional bitmap publication and original 9F sound request. Removing these
two lines reconstructs the exact v0070 production main. Other production
assets and the free-healer timing code are unchanged.

The natural first-page scroll now has identical lists of complete VRAM-pose
frames, not merely matching first appearances:

| Shift | NTSC source and native | PAL source and native |
| --- | --- | --- |
| 2 pixels | 2202,2203 | 2202 |
| 5 pixels | 2205,2206 | 2204 |
| 8 pixels | 2208,2209 | 2206 |
| 10 pixels | 2211..2214 | 2208..2210 |

All 130 tile patterns (8320 pixel colors) agree at each complete pose.
Partially uploaded frames, subsequent words and the complete framebuffer
are not established as identical. Native software-bitmap mutation timing
can still differ from the source even where the visible complete pose agrees.

Current-ROM regression: twelve final acknowledgements in PAL/NTSC, six NPC
conversations plus one natural walking route, existing bounded hero/scroll
and eight deterministic enemy-motion comparisons in both regions. Merchant,
save and free-night evidence remains associated with v0070, not rerun here.

New natural timing diagnostics remain deliberately separate from passing
checks. Relative to the source, the native opening text routine is entered
40 frames early in NTSC / 39 PAL; the first page wait begins 53 / 48 frames
early; the first room becomes active 33 / 31 frames early. Source 1197..11B4
performs music handling, equipment palette preparation, font loading and
0AA4 palette fade before entering 7444. Native opening_dialogue currently
calls show_dialogue_text directly. Profile these missing setup stages next,
instead of masking their duration with a fixed startup delay.

tools/profile_world_clock.py now preserves full ROM PC addresses for native
instruction-entry observations; only RAM reads use the low sixteen bits.
Earlier profiles could miss functions above 64 KiB, including render text.
The archived new profiles contain the actual render and room-loader entries.

Global inter-page clock resets, source IRQ suppression, initial loading,
natural complete progression, all abilities, quests, full enemy/boss behavior,
ending, complete visuals and audio waveform fidelity remain unfinished.
