# Staged dialogue scroll and free-night timing - v0070

ROM SHA-256 ee7ae2e440037232e650fae4a30b1c0ce4a2ad1f1e955e46e9a261d88074d008, 512 KiB,
additive checksum 1E6C. Intermediate v0065-v0069 retained as build-only.

The two native line-scroll paths now publish the source 068A..06B6 sequence:
two, three, three, two pixels, with a bitmap upload after each step. Previously
the ten-pixel movement happened in one CPU operation and the next word was
drawn before publishing the empty final pose.

The monochrome dialogue renderer now converts each original bitmap byte
through a 256-row packed-pixel table. Every table row is checked against SMS
planes FF / bitmap / 00 / 00, yielding exactly color indices 1 and 3. The
continuation marker updates one tile-map word instead of rebuilding/uploading
the entire 768-word map. These changes reduce native rendering work without
substituting captured screens or running source Z80 instructions.

Natural opening test, first complete VRAM appearance of each cumulative pose:

| Region | 2 pixels | 5 pixels | 8 pixels | 10 pixels |
| --- | --- | --- | --- | --- |
| NTSC SMS and MD | 2202 | 2205 | 2208 | 2211 |
| PAL SMS and MD | 2202 | 2204 | 2206 | 2208 |

All 130 tile patterns, 8320 pixel colors per pose, agree with the original.
The last pose persists longer on SMS before the next word appears; complete
dialogue timing is not yet equal. Inter-page global-clock resets and initial
loading duration also remain unresolved. The test uses normal controller
input with no RAM injection, and records all observed pose frames.

Free-healer timing checks exposed a one-frame fade/restore discrepancy.
Separate read-only source/native instruction profiles establish that source
76C3 reaches the display-disable path at 3719 NTSC and 3718 PAL for the
controlled ordinary-life case after confirmation at 3700. The free service
now retains that fade work budget and at least 62 blackout frames, including
the original 60-IRQ night plus HUD/map restoration. Five cases per region
(low life, larger capacity, full life, refusal, simultaneous confirm/down)
compare the entire display-disabled interval to SMS. Paid-night timing is
not claimed exact by this change.

Current-ROM checks also cover the twelve opening final-acknowledgement cases,
six NPC conversations plus a natural walking route, all merchant fixtures,
three save slots with cold Continue and cancellation/death paths, and the
existing bounded hero/scroll/eight-enemy timing comparisons in both regions.
See validation/dialogue_scroll_patch_audit.json for hashes and scope.

The patch audit reconstructs the exact v0064 main and previous healer include
by removing these changes, and checks all other previous production assets.
Full natural progression, all abilities, quests, enemy/boss behavior, ending,
complete framebuffers and audio waveform fidelity remain unfinished.
